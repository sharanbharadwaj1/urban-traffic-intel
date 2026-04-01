import cv2

import config


class TrackSnapshotBuffer:

    def __init__(self):

        self.snapshots = {}

    def _score_snapshot(self, frame, bbox):

        x1, y1, x2, y2 = map(int, bbox)
        height, width = frame.shape[:2]
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(x1 + 1, min(x2, width))
        y2 = max(y1 + 1, min(y2, height))

        crop = frame[y1:y2, x1:x2]

        if crop.size == 0:
            return float("-inf"), None

        crop_h, crop_w = crop.shape[:2]
        area_score = crop_w * crop_h
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        center_y = (y1 + y2) / 2.0
        center_bias = 1.0 - abs((center_y / max(height, 1)) - 0.6)

        score = area_score + (blur_score * 20.0) + (center_bias * 1000.0)
        return score, crop

    def add(self, track_id, frame_id, frame, bbox, metadata=None):

        score, crop = self._score_snapshot(frame, bbox)

        if crop is None:
            return

        entry = {
            "frame_id": frame_id,
            "bbox": bbox,
            "score": score,
            "frame": frame.copy(),
            "crop": crop,
            "metadata": metadata or {},
        }

        items = self.snapshots.setdefault(track_id, [])
        items.append(entry)
        items.sort(key=lambda item: item["score"], reverse=True)

        if len(items) > config.PLATE_TRACK_BUFFER_SIZE:
            del items[config.PLATE_TRACK_BUFFER_SIZE:]

    def best(self, track_id):

        return list(self.snapshots.get(track_id, []))[:config.PLATE_TRACK_PROCESS_TOP_K]

    def clear(self, track_id):

        self.snapshots.pop(track_id, None)

    def prune(self, current_frame_id):

        expired = []

        for track_id, items in list(self.snapshots.items()):
            fresh_items = [
                item
                for item in items
                if (current_frame_id - item["frame_id"]) <= config.PLATE_TRACK_TTL_FRAMES
            ]

            if fresh_items:
                self.snapshots[track_id] = fresh_items
            else:
                expired.append(track_id)
                self.snapshots.pop(track_id, None)

        return expired
