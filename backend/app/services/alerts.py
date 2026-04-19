from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime

from app.core.config import Settings
from app.services.tracking import TrackedObject


@dataclass
class EventPayload:
    event_type: str
    timestamp: datetime
    frame_index: int
    track_id: int | None
    class_name: str | None
    confidence: float | None
    bbox: dict | None
    metadata: dict


class AlertService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.track_history: dict[int, deque[tuple[float, float]]] = defaultdict(
            lambda: deque(maxlen=self.settings.stationary_frame_window)
        )
        self.stationary_alerted: set[int] = set()

    def evaluate(
        self,
        frame_index: int,
        timestamp: datetime,
        tracked_objects: list[TrackedObject],
    ) -> list[EventPayload]:
        events: list[EventPayload] = []

        for tracked in tracked_objects:
            self.track_history[tracked.track_id].append(tracked.center)

            if tracked.class_name in self.settings.alert_class_set:
                events.append(
                    EventPayload(
                        event_type="object_detected",
                        timestamp=timestamp,
                        frame_index=frame_index,
                        track_id=tracked.track_id,
                        class_name=tracked.class_name,
                        confidence=tracked.confidence,
                        bbox=tracked.bbox_dict,
                        metadata={"source": "inference"},
                    )
                )

            history = self.track_history[tracked.track_id]
            if len(history) < self.settings.stationary_frame_window:
                continue

            xs = [value[0] for value in history]
            ys = [value[1] for value in history]
            span_x = max(xs) - min(xs)
            span_y = max(ys) - min(ys)
            if span_x <= self.settings.stationary_pixel_threshold and span_y <= self.settings.stationary_pixel_threshold:
                if tracked.track_id not in self.stationary_alerted:
                    self.stationary_alerted.add(tracked.track_id)
                    events.append(
                        EventPayload(
                            event_type="stationary_object",
                            timestamp=timestamp,
                            frame_index=frame_index,
                            track_id=tracked.track_id,
                            class_name=tracked.class_name,
                            confidence=tracked.confidence,
                            bbox=tracked.bbox_dict,
                            metadata={
                                "window": self.settings.stationary_frame_window,
                                "movement_px": {"x": span_x, "y": span_y},
                            },
                        )
                    )
            else:
                self.stationary_alerted.discard(tracked.track_id)

        return events
