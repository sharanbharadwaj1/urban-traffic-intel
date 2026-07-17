import logging
from dataclasses import dataclass
from time import perf_counter

import numpy as np

from app.core.config import Settings

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None


logger = logging.getLogger(__name__)


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: list[float]


class InferenceService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None
        self._class_names: dict[int, str] = {}

    @property
    def is_model_available(self) -> bool:
        return YOLO is not None

    def _load_model(self):
        if self._model is None:
            if YOLO is None:
                raise RuntimeError("Ultralytics is not installed. Install project requirements to enable inference.")
            self._model = YOLO(self.settings.model_path)
            names = getattr(self._model.model, "names", None) or getattr(self._model, "names", {})
            if isinstance(names, dict):
                self._class_names = {int(key): str(value) for key, value in names.items()}
            else:
                self._class_names = {index: str(value) for index, value in enumerate(names)}
        return self._model

    def infer(self, frame: np.ndarray) -> tuple[list[Detection], float]:
        model = self._load_model()
        start = perf_counter()
        results = model.predict(frame, verbose=False, conf=self.settings.confidence_threshold)
        duration_ms = round((perf_counter() - start) * 1000, 2)

        detections: list[Detection] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                class_id = int(box.cls.item())
                class_name = self._class_names.get(class_id, str(class_id))
                if self.settings.class_filter_set and class_name not in self.settings.class_filter_set:
                    continue
                detections.append(
                    Detection(
                        class_id=class_id,
                        class_name=class_name,
                        confidence=round(float(box.conf.item()), 4),
                        bbox=[round(float(value), 2) for value in box.xyxy[0].tolist()],
                    )
                )

        logger.info(
            "inference_completed",
            extra={
                "inference_time_ms": duration_ms,
                "detected_objects": [d.class_name for d in detections],
                "detections_count": len(detections),
            },
        )
        return detections, duration_ms
