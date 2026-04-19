import math
from dataclasses import dataclass

from app.services.inference import Detection


@dataclass
class TrackedObject:
    track_id: int
    class_name: str
    confidence: float
    bbox: list[float]

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    @property
    def bbox_dict(self) -> dict:
        x1, y1, x2, y2 = self.bbox
        return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}


class SimpleTracker:
    def __init__(self, max_distance: float = 80.0) -> None:
        self.max_distance = max_distance
        self.next_track_id = 1
        self.active_tracks: dict[int, TrackedObject] = {}

    def update(self, detections: list[Detection]) -> list[TrackedObject]:
        tracked: list[TrackedObject] = []
        unmatched_tracks = set(self.active_tracks.keys())

        for detection in detections:
            match_id = self._match_track(detection)
            if match_id is None:
                match_id = self.next_track_id
                self.next_track_id += 1

            tracked_object = TrackedObject(
                track_id=match_id,
                class_name=detection.class_name,
                confidence=detection.confidence,
                bbox=detection.bbox,
            )
            self.active_tracks[match_id] = tracked_object
            unmatched_tracks.discard(match_id)
            tracked.append(tracked_object)

        for track_id in unmatched_tracks:
            self.active_tracks.pop(track_id, None)

        return tracked

    def _match_track(self, detection: Detection) -> int | None:
        best_track_id = None
        best_distance = self.max_distance
        detection_center = self._center(detection.bbox)

        for track_id, track in self.active_tracks.items():
            if track.class_name != detection.class_name:
                continue
            distance = math.dist(detection_center, track.center)
            if distance <= best_distance:
                best_distance = distance
                best_track_id = track_id

        return best_track_id

    @staticmethod
    def _center(bbox: list[float]) -> tuple[float, float]:
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
