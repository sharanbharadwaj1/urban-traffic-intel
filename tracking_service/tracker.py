import supervision as sv
import numpy as np


class Tracker:

    def __init__(self):

        self.tracker = sv.ByteTrack()

    def update(self, detections):

        boxes = []
        scores = []
        classes = []

        for d in detections:

            boxes.append(d["bbox"])
            scores.append(d["confidence"])
            classes.append(d["class_id"])

        if len(boxes) == 0:
            return []

        detections_sv = sv.Detections(
            xyxy=np.array(boxes),
            confidence=np.array(scores),
            class_id=np.array(classes)
        )

        tracked = self.tracker.update_with_detections(detections_sv)

        objects = []

        for i in range(len(tracked.xyxy)):

            obj = {
                "track_id": int(tracked.tracker_id[i]),
                "class_id": int(tracked.class_id[i]),
                "confidence": float(tracked.confidence[i]),
                "bbox": tracked.xyxy[i].tolist()
            }

            objects.append(obj)

        return objects


# import supervision as sv
# import numpy as np

# class Tracker:

#     def __init__(self):

#         self.tracker = sv.ByteTrack()

#     def update(self, detections):

#         boxes = []
#         scores = []
#         classes = []

#         for d in detections:

#             boxes.append(d["bbox"])
#             scores.append(d["confidence"])
#             classes.append(d["class_id"])

#         detections_sv = sv.Detections(
#             xyxy=np.array(boxes),
#             confidence=np.array(scores),
#             class_id=np.array(classes)
#         )

#         tracks = self.tracker.update_with_detections(detections_sv)

#         return tracks