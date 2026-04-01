import numpy as np
import supervision as sv


class Tracker:

    def __init__(self):
        self.tracker = sv.ByteTrack()
        self.raw_to_stable = {}
        self.stable_tracks = {}
        self.next_stable_id = 1
        self.max_track_gap = 30
        self.min_reuse_iou = 0.25
        self.max_center_distance = 180.0
        self.duplicate_iou_threshold = 0.7
        self.minimum_confidence = 0.2

    def update(self, detections, frame_id=None):
        detections = self._deduplicate_detections(detections)

        boxes = []
        scores = []
        classes = []

        for detection in detections:
            if detection["confidence"] < self.minimum_confidence:
                continue
            boxes.append(detection["bbox"])
            scores.append(detection["confidence"])
            classes.append(detection["class_id"])

        if len(boxes) == 0:
            self._prune_tracks(frame_id, set())
            return []

        detections_sv = sv.Detections(
            xyxy=np.array(boxes),
            confidence=np.array(scores),
            class_id=np.array(classes),
        )

        tracked = self.tracker.update_with_detections(detections_sv)

        objects = []
        active_stable_ids = set()

        for i in range(len(tracked.xyxy)):
            raw_track_id = int(tracked.tracker_id[i])
            bbox = tracked.xyxy[i].tolist()
            class_id = int(tracked.class_id[i])
            stable_track_id = self._assign_stable_id(raw_track_id, bbox, class_id, frame_id)

            obj = {
                "track_id": stable_track_id,
                "class_id": class_id,
                "confidence": float(tracked.confidence[i]),
                "bbox": bbox,
            }

            objects.append(obj)
            active_stable_ids.add(stable_track_id)

        self._prune_tracks(frame_id, active_stable_ids)
        return objects

    def _assign_stable_id(self, raw_track_id, bbox, class_id, frame_id):
        stable_track_id = self.raw_to_stable.get(raw_track_id)
        if stable_track_id is None:
            stable_track_id = self._match_existing_track(bbox, class_id, frame_id)
            if stable_track_id is None:
                stable_track_id = self.next_stable_id
                self.next_stable_id += 1
            self.raw_to_stable[raw_track_id] = stable_track_id

        track = dict(self.stable_tracks.get(stable_track_id, {}))
        track.update({
            "bbox": bbox,
            "class_id": self._update_class_vote(stable_track_id, class_id),
            "last_seen": frame_id if frame_id is not None else 0,
        })
        class_votes = self.stable_tracks.get(stable_track_id, {}).get("class_votes")
        if class_votes is not None:
            track["class_votes"] = class_votes
        self.stable_tracks[stable_track_id] = track
        return stable_track_id

    def _match_existing_track(self, bbox, class_id, frame_id):
        if frame_id is None:
            return None

        best_track_id = None
        best_score = 0.0

        for stable_track_id, track in self.stable_tracks.items():
            if not self._same_tracking_family(track["class_id"], class_id):
                continue
            if frame_id - track["last_seen"] > self.max_track_gap:
                continue

            iou = self._iou(bbox, track["bbox"])
            distance = self._center_distance(bbox, track["bbox"])
            if iou < self.min_reuse_iou and distance > self.max_center_distance:
                continue

            score = iou - (distance / max(self.max_center_distance, 1.0)) * 0.08
            if score > best_score:
                best_score = score
                best_track_id = stable_track_id

        return best_track_id

    def _update_class_vote(self, stable_track_id, class_id):
        track = self.stable_tracks.get(stable_track_id, {})
        class_votes = dict(track.get("class_votes", {}))
        class_votes[class_id] = class_votes.get(class_id, 0) + 1
        dominant_class_id = max(class_votes.items(), key=lambda item: item[1])[0]

        track["class_votes"] = class_votes
        track["class_id"] = dominant_class_id
        self.stable_tracks[stable_track_id] = track
        return dominant_class_id

    def _prune_tracks(self, frame_id, active_stable_ids):
        if frame_id is None:
            return

        stale_ids = [
            stable_track_id
            for stable_track_id, track in self.stable_tracks.items()
            if frame_id - track["last_seen"] > self.max_track_gap
        ]
        for stable_track_id in stale_ids:
            self.stable_tracks.pop(stable_track_id, None)

        stale_raw_ids = [
            raw_track_id
            for raw_track_id, stable_track_id in self.raw_to_stable.items()
            if stable_track_id not in self.stable_tracks and stable_track_id not in active_stable_ids
        ]
        for raw_track_id in stale_raw_ids:
            self.raw_to_stable.pop(raw_track_id, None)

    def _deduplicate_detections(self, detections):
        if not detections:
            return []

        kept = []
        for detection in sorted(detections, key=lambda item: item["confidence"], reverse=True):
            is_duplicate = False
            for existing in kept:
                if not self._same_tracking_family(existing["class_id"], detection["class_id"]):
                    continue
                if self._iou(existing["bbox"], detection["bbox"]) >= self.duplicate_iou_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                kept.append(detection)
        return kept

    @staticmethod
    def _same_tracking_family(class_a, class_b):
        four_wheelers = {2, 5, 7}
        two_wheelers = {3}

        if class_a in four_wheelers and class_b in four_wheelers:
            return True
        if class_a in two_wheelers and class_b in two_wheelers:
            return True
        return class_a == class_b

    @staticmethod
    def _iou(box_a, box_b):
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h

        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union_area = area_a + area_b - inter_area

        if union_area <= 0:
            return 0.0
        return inter_area / union_area

    @staticmethod
    def _center_distance(box_a, box_b):
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        center_a = ((ax1 + ax2) / 2.0, (ay1 + ay2) / 2.0)
        center_b = ((bx1 + bx2) / 2.0, (by1 + by2) / 2.0)
        return float(np.hypot(center_a[0] - center_b[0], center_a[1] - center_b[1]))
