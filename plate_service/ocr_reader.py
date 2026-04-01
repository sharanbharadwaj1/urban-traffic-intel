import re

import cv2
from pathlib import Path

from PIL import Image

import config


INDIAN_PLATE_REGEX = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{3,4}$")
NON_ALNUM_REGEX = re.compile(r"[^A-Z0-9]")


class OCRReader:

    def __init__(self):

        self.primary_backend = None
        self.primary_reader = None
        self.fallback_reader = None

        if config.OCR_BACKEND == "paddle":
            self.primary_backend, self.primary_reader = self._init_paddle()

            if config.OCR_USE_FALLBACK:
                _, self.fallback_reader = self._init_easyocr()
        else:
            self.primary_backend, self.primary_reader = self._init_easyocr()

    def _init_paddle(self):

        try:
            from paddleocr import PaddleOCR
        except ImportError:
            print("PaddleOCR not installed, falling back to EasyOCR.")
            return self._init_easyocr()

        constructor_variants = [
            {
                "lang": config.OCR_LANG,
                "use_textline_orientation": config.OCR_USE_ANGLE_CLS,
            },
            {
                "lang": config.OCR_LANG,
                "use_angle_cls": config.OCR_USE_ANGLE_CLS,
            },
            {
                "lang": config.OCR_LANG,
            },
        ]

        last_error = None
        try:
            for kwargs in constructor_variants:
                try:
                    reader = PaddleOCR(**kwargs)
                    return "paddle", reader
                except (TypeError, ValueError) as exc:
                    last_error = exc
                    continue
        except Exception as exc:
            last_error = exc

        print(f"PaddleOCR init failed, falling back to EasyOCR: {last_error}")
        return self._init_easyocr()


    def _init_easyocr(self):

        try:
            import easyocr
        except ImportError:
            print("EasyOCR not installed.")
            return None, None

        reader = easyocr.Reader([config.OCR_LANG], gpu=config.OCR_USE_GPU)
        return "easyocr", reader

    def _normalize_text(self, text):

        cleaned = NON_ALNUM_REGEX.sub("", text.upper())

        if not cleaned:
            return None

        if len(cleaned) < config.PLATE_MIN_LENGTH or len(cleaned) > config.PLATE_MAX_LENGTH:
            return None

        if not any(ch.isalpha() for ch in cleaned) or not any(ch.isdigit() for ch in cleaned):
            return None

        return cleaned

    def _score_text(self, text, confidence):

        score = float(confidence)

        if INDIAN_PLATE_REGEX.match(text):
            score += 1.5

        if 8 <= len(text) <= 10:
            score += 0.5

        prefix_letters = sum(ch.isalpha() for ch in text[:2])
        if prefix_letters == min(2, len(text)):
            score += 0.2

        return score

    def _generate_variants(self, image):

        if image is None or image.size == 0:
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        binary = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )
        inverted = cv2.bitwise_not(binary)

        return [image, gray, enhanced, binary, inverted]

    def _read_with_paddle(self, image):

        try:
            results = self.primary_reader.ocr(
                image,
                use_textline_orientation=config.OCR_USE_ANGLE_CLS,
            )
        except (TypeError, ValueError):
            try:
                results = self.primary_reader.ocr(image, cls=config.OCR_USE_ANGLE_CLS)
            except (TypeError, ValueError):
                results = self.primary_reader.ocr(image)
        candidates = []

        for line in results or []:
            for item in line or []:
                text = item[1][0]
                confidence = item[1][1]
                candidates.append((text, confidence))

        return candidates

    def _read_with_easyocr(self, image, reader):

        results = reader.readtext(
            image,
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            paragraph=False,
            detail=1,
            decoder="beamsearch",
        )

        return [(text, confidence) for _, text, confidence in results]

    def debug_dump(self, image, prefix, texts):

        if not config.PLATE_DEBUG:
            return

        debug_dir = Path(__file__).resolve().parents[1] / config.PLATE_DEBUG_DIR
        debug_dir.mkdir(exist_ok=True)
        image_path = debug_dir / f"{prefix}.jpg"
        text_path = debug_dir / f"{prefix}.txt"

        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        pil_image.save(image_path, quality=95)
        text_path.write_text("\n".join(texts), encoding="utf-8")

    def _candidate_texts(self, image):

        if self.primary_reader is None:
            return []

        if self.primary_backend == "paddle":
            try:
                return self._read_with_paddle(image)
            except Exception as exc:
                print(f"PaddleOCR inference failed, falling back: {exc}")
                return self._fallback_texts(image)

        return self._read_with_easyocr(image, self.primary_reader)

    def _fallback_texts(self, image):

        if self.fallback_reader is None:
            return []

        return self._read_with_easyocr(image, self.fallback_reader)

    def read_plate(self, image):

        best_text = None
        best_score = float("-inf")
        debug_texts = []

        for variant in self._generate_variants(image):
            for text, confidence in self._candidate_texts(variant):
                normalized = self._normalize_text(text)
                debug_texts.append(
                    f"primary raw={text!r} normalized={normalized!r} confidence={confidence}"
                )

                if not normalized:
                    continue

                score = self._score_text(normalized, confidence)

                if score > best_score:
                    best_text = normalized
                    best_score = score

            if best_text:
                continue

            for text, confidence in self._fallback_texts(variant):
                normalized = self._normalize_text(text)
                debug_texts.append(
                    f"fallback raw={text!r} normalized={normalized!r} confidence={confidence}"
                )

                if not normalized:
                    continue

                score = self._score_text(normalized, confidence)

                if score > best_score:
                    best_text = normalized
                    best_score = score

        if debug_texts:
            self.debug_dump(image, f"ocr_debug_{id(image)}", debug_texts)

        return best_text
