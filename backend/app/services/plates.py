import json
import re
import time
import uuid
from collections import defaultdict
from urllib import error, request

import cv2
import numpy as np

from app.core.config import Settings
from app.services.tracking import TrackedObject


class PlateService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pending_reads: dict[int, dict[str, int]] = defaultdict(dict)
        self.attempt_counts: dict[int, int] = {}
        self.next_attempt_frame: dict[int, int] = {}
        self.snapshots: dict[int, list[dict]] = {}
        self.track_plates: dict[int, str] = {}
        self.last_request_at = 0.0
        self.eligible_classes = {"car", "bus", "truck"}

    @property
    def enabled(self) -> bool:
        return self.settings.plate_enabled and bool(self.settings.anpr_api_url)

    def get_plate(self, track_id: int) -> str | None:
        return self.track_plates.get(track_id)

    def process_track(
        self,
        tracked_object: TrackedObject,
        frame_index: int,
        frame: np.ndarray,
    ) -> str | None:
        if not self.enabled or tracked_object.class_name not in self.eligible_classes:
            return None
        if tracked_object.track_id in self.track_plates:
            return self.track_plates[tracked_object.track_id]

        self._add_snapshot(tracked_object.track_id, frame_index, frame, tracked_object.bbox)
        for expired_track_id in self._prune(frame_index):
            self.pending_reads.pop(expired_track_id, None)
            self.attempt_counts.pop(expired_track_id, None)
            self.next_attempt_frame.pop(expired_track_id, None)

        attempts = self.attempt_counts.get(tracked_object.track_id, 0)
        if attempts >= self.settings.plate_track_max_attempts:
            self._clear_track(tracked_object.track_id)
            return None

        retry_at = self.next_attempt_frame.get(tracked_object.track_id, 0)
        if frame_index < retry_at:
            return None

        plate = None
        for snapshot in self.snapshots.get(tracked_object.track_id, [])[: self.settings.plate_track_process_top_k]:
            plate = self._detect_plate(snapshot["frame"], snapshot["bbox"])
            if plate:
                break

        self.attempt_counts[tracked_object.track_id] = attempts + 1
        self.next_attempt_frame[tracked_object.track_id] = frame_index + self.settings.plate_retry_cooldown_frames

        if not plate:
            return None

        track_reads = self.pending_reads[tracked_object.track_id]
        track_reads[plate] = track_reads.get(plate, 0) + 1
        if track_reads[plate] >= self.settings.plate_confirmation_reads:
            self.track_plates[tracked_object.track_id] = plate
            self._clear_track(tracked_object.track_id, keep_plate=True)
            return plate
        return None

    def _clear_track(self, track_id: int, keep_plate: bool = False) -> None:
        self.snapshots.pop(track_id, None)
        self.pending_reads.pop(track_id, None)
        self.attempt_counts.pop(track_id, None)
        self.next_attempt_frame.pop(track_id, None)
        if not keep_plate:
            self.track_plates.pop(track_id, None)

    def _add_snapshot(self, track_id: int, frame_id: int, frame: np.ndarray, bbox: list[float]) -> None:
        score, _ = self._score_snapshot(frame, bbox)
        entry = {
            "frame_id": frame_id,
            "bbox": bbox,
            "score": score,
            "frame": frame.copy(),
        }
        items = self.snapshots.setdefault(track_id, [])
        items.append(entry)
        items.sort(key=lambda item: item["score"], reverse=True)
        if len(items) > self.settings.plate_track_buffer_size:
            del items[self.settings.plate_track_buffer_size :]

    def _score_snapshot(self, frame: np.ndarray, bbox: list[float]) -> tuple[float, np.ndarray | None]:
        x1, y1, x2, y2 = map(int, bbox)
        height, width = frame.shape[:2]
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(x1 + 1, min(x2, width))
        y2 = max(y1 + 1, min(y2, height))
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return float("-inf"), None
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        area_score = crop.shape[0] * crop.shape[1]
        center_y = (y1 + y2) / 2.0
        center_bias = 1.0 - abs((center_y / max(height, 1)) - 0.6)
        return area_score + (blur_score * 20.0) + (center_bias * 1000.0), crop

    def _prune(self, current_frame_id: int) -> list[int]:
        expired = []
        for track_id, items in list(self.snapshots.items()):
            fresh = [
                item
                for item in items
                if (current_frame_id - item["frame_id"]) <= self.settings.plate_track_ttl_frames
            ]
            if fresh:
                self.snapshots[track_id] = fresh
            else:
                expired.append(track_id)
                self.snapshots.pop(track_id, None)
        return expired

    def _detect_plate(self, frame: np.ndarray, bbox: list[float]) -> str | None:
        payload = self._request_payload(frame)
        best_plate = None
        best_score = float("-inf")
        target_box = tuple(map(float, bbox))
        for result in payload.get("results", []):
            plate = self._normalize_plate(result.get("plate"))
            score = float(result.get("score", 0.0))
            dscore = float(result.get("dscore", 0.0))
            vehicle = result.get("vehicle") or {}
            vehicle_box = vehicle.get("box")
            if not plate or score < self.settings.anpr_min_score or not vehicle_box:
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

    def _request_payload(self, image: np.ndarray) -> dict:
        ok, buffer = cv2.imencode(".jpg", image)
        if not ok:
            return {}
        now = time.monotonic()
        wait_seconds = self.settings.anpr_min_interval_seconds - (now - self.last_request_at)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        boundary = f"----CodexBoundary{uuid.uuid4().hex}"
        body = self._build_multipart_body(boundary, buffer.tobytes())
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        if self.settings.anpr_api_token:
            headers["Authorization"] = f"Token {self.settings.anpr_api_token}"
        req = request.Request(self.settings.anpr_api_url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.settings.anpr_timeout_seconds) as response:
                self.last_request_at = time.monotonic()
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            if exc.code == 429:
                self.last_request_at = time.monotonic() + self.settings.anpr_retry_backoff_seconds
            else:
                self.last_request_at = time.monotonic()
            return {}
        except (error.URLError, TimeoutError, json.JSONDecodeError):
            self.last_request_at = time.monotonic()
            return {}

    def _build_multipart_body(self, boundary: str, image_bytes: bytes) -> bytes:
        parts: list[bytes] = [
            f"--{boundary}\r\n".encode("utf-8"),
            b'Content-Disposition: form-data; name="upload"; filename="plate.jpg"\r\n',
            b"Content-Type: image/jpeg\r\n\r\n",
            image_bytes,
            b"\r\n",
        ]
        if self.settings.anpr_country:
            parts.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    b'Content-Disposition: form-data; name="regions"\r\n\r\n',
                    f"{self.settings.anpr_country}\r\n".encode("utf-8"),
                ]
            )
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        return b"".join(parts)

    def _normalize_plate(self, text: str | None) -> str | None:
        if not text:
            return None
        cleaned = re.sub(r"[^A-Z0-9]", "", str(text).upper())
        if len(cleaned) < self.settings.plate_min_length or len(cleaned) > self.settings.plate_max_length:
            return None
        if sum(char.isalpha() for char in cleaned) < 2 or sum(char.isdigit() for char in cleaned) < 2:
            return None
        return cleaned

    @staticmethod
    def _overlap_ratio(box_a: tuple[float, float, float, float], box_b: tuple[float, float, float, float]) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)
        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0
        inter = (ix2 - ix1) * (iy2 - iy1)
        area_a = max((ax2 - ax1) * (ay2 - ay1), 1.0)
        return inter / area_a

    @staticmethod
    def _center_distance_score(box_a: tuple[float, float, float, float], box_b: tuple[float, float, float, float]) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        acx = (ax1 + ax2) / 2.0
        acy = (ay1 + ay2) / 2.0
        bcx = (bx1 + bx2) / 2.0
        bcy = (by1 + by2) / 2.0
        distance = ((acx - bcx) ** 2 + (acy - bcy) ** 2) ** 0.5
        diagonal = max(((ax2 - ax1) ** 2 + (ay2 - ay1) ** 2) ** 0.5, 1.0)
        return max(0.0, 1.0 - (distance / diagonal))
