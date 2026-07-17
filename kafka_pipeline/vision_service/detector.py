from ultralytics import YOLO

class Detector:

    def __init__(self, model_name):
        self.model = YOLO(model_name)

    def detect(self, frame):

        results = self.model(frame)[0]

        detections = []

        for box in results.boxes:

            cls = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()

            detections.append({
                "class_id": cls,
                "confidence": conf,
                "bbox": xyxy
            })

        return detections