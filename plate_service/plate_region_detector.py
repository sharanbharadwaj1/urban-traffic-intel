from pathlib import Path

import cv2

import config


class PlateRegionDetector:

    def __init__(self):

        self.model_path = Path(__file__).resolve().parents[1] / config.PLATE_DETECTOR_MODEL
        self.model = None

        if not self.model_path.exists():
            print(f"Plate detector model not found: {self.model_path}")
            return

        try:
            from ultralytics import YOLO
        except ImportError:
            print("Ultralytics is not installed; plate detector disabled.")
            return

        self.model = YOLO(str(self.model_path))

    def available(self):

        return self.model is not None

    def detect(self, vehicle_image):

        if self.model is None or vehicle_image is None or vehicle_image.size == 0:
            return []

        results = self.model.predict(
            source=vehicle_image,
            conf=config.PLATE_DETECTOR_CONFIDENCE,
            imgsz=config.PLATE_DETECTOR_IMGSZ,
            verbose=False,
            device=0 if config.PLATE_DETECTOR_USE_GPU else "cpu",
        )

        boxes = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                boxes.append((confidence, int(x1), int(y1), int(x2), int(y2)))

        boxes.sort(reverse=True)
        crops = []

        for _, x1, y1, x2, y2 in boxes:
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(vehicle_image.shape[1], x2)
            y2 = min(vehicle_image.shape[0], y2)

            if x2 <= x1 or y2 <= y1:
                continue

            crop = vehicle_image[y1:y2, x1:x2]

            if crop.size:
                crops.append(crop)

        return crops
