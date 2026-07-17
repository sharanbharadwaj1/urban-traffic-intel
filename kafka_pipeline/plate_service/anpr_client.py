import json
import time
import uuid
from urllib import error, request

import cv2

import config


class ANPRClient:

    def __init__(self):

        self.api_url = config.ANPR_API_URL
        self.api_token = config.ANPR_API_TOKEN
        self.country = config.ANPR_COUNTRY
        self.min_score = config.ANPR_MIN_SCORE
        self.timeout = config.ANPR_TIMEOUT_SECONDS
        self.min_interval = config.ANPR_MIN_INTERVAL_SECONDS
        self.retry_backoff = config.ANPR_RETRY_BACKOFF_SECONDS
        self.last_request_at = 0.0

    def _encode_image(self, image):

        ok, buffer = cv2.imencode(".jpg", image)

        if not ok:
            return None

        return buffer.tobytes()

    def _build_multipart_body(self, image_bytes):

        boundary = f"----CodexBoundary{uuid.uuid4().hex}"
        parts = []

        def add_text(name, value):
            parts.append(f"--{boundary}\r\n".encode("utf-8"))
            parts.append(
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8")
            )
            parts.append(f"{value}\r\n".encode("utf-8"))

        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(
            b'Content-Disposition: form-data; name="upload"; filename="plate.jpg"\r\n'
        )
        parts.append(b"Content-Type: image/jpeg\r\n\r\n")
        parts.append(image_bytes)
        parts.append(b"\r\n")

        if self.country:
            add_text("regions", self.country)

        parts.append(f"--{boundary}--\r\n".encode("utf-8"))

        return boundary, b"".join(parts)

    def _normalize_plate(self, plate):

        if not plate:
            return None

        normalized = "".join(ch for ch in plate.upper() if ch.isalnum())
        return normalized or None

    def _request_payload(self, image):

        image_bytes = self._encode_image(image)

        if not image_bytes:
            return {}

        now = time.monotonic()
        wait_seconds = self.min_interval - (now - self.last_request_at)
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        boundary, body = self._build_multipart_body(image_bytes)
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }

        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"

        req = request.Request(
            self.api_url,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                self.last_request_at = time.monotonic()
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            if exc.code == 429:
                print("ANPR rate limited, backing off.")
                self.last_request_at = time.monotonic() + self.retry_backoff
            else:
                self.last_request_at = time.monotonic()
            print("ANPR request failed:", exc)
            return {}
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.last_request_at = time.monotonic()
            print("ANPR request failed:", exc)
            return {}

    def _overlap_ratio(self, box_a, box_b):

        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0

        inter = (ix2 - ix1) * (iy2 - iy1)
        area_a = max((ax2 - ax1) * (ay2 - ay1), 1)
        return inter / area_a

    def _center_distance_score(self, box_a, box_b):

        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        acx = (ax1 + ax2) / 2.0
        acy = (ay1 + ay2) / 2.0
        bcx = (bx1 + bx2) / 2.0
        bcy = (by1 + by2) / 2.0
        distance = ((acx - bcx) ** 2 + (acy - bcy) ** 2) ** 0.5
        diagonal = max(((ax2 - ax1) ** 2 + (ay2 - ay1) ** 2) ** 0.5, 1.0)
        normalized_distance = distance / diagonal
        return max(0.0, 1.0 - normalized_distance)

    def read_plate(self, image):

        payload = self._request_payload(image)
        best_plate = None
        best_score = float("-inf")

        for result in payload.get("results", []):
            plate = self._normalize_plate(result.get("plate"))
            score = float(result.get("score", 0.0))
            dscore = float(result.get("dscore", 0.0))
            combined_score = score + dscore

            if not plate or score < self.min_score:
                continue

            if combined_score > best_score:
                best_plate = plate
                best_score = combined_score

        return best_plate

    def read_plate_for_bbox(self, image, bbox):

        payload = self._request_payload(image)
        best_plate = None
        best_score = float("-inf")
        target_box = tuple(map(float, bbox))

        for result in payload.get("results", []):
            plate = self._normalize_plate(result.get("plate"))
            score = float(result.get("score", 0.0))
            dscore = float(result.get("dscore", 0.0))
            vehicle = result.get("vehicle") or {}
            vehicle_box = vehicle.get("box")

            if not plate or score < self.min_score or not vehicle_box:
                continue

            candidate_box = (
                float(vehicle_box.get("xmin", 0.0)),
                float(vehicle_box.get("ymin", 0.0)),
                float(vehicle_box.get("xmax", 0.0)),
                float(vehicle_box.get("ymax", 0.0)),
            )
            overlap = self._overlap_ratio(target_box, candidate_box)
            center_score = self._center_distance_score(target_box, candidate_box)
            combined_score = score + dscore + overlap + center_score

            if overlap <= 0.02 and center_score <= 0.25:
                continue

            if combined_score > best_score:
                best_plate = plate
                best_score = combined_score

        return best_plate
