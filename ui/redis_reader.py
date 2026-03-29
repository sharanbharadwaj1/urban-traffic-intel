import json

import redis


class RedisReader:

    def __init__(self, host="localhost", port=6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)

    def get_camera_ids(self, count=100):
        messages = self.redis.xrevrange("tracked_objects", count=count)
        camera_ids = []

        for _, msg in messages:
            payload = json.loads(msg["payload"])
            camera_id = payload.get("camera_id")

            if camera_id and camera_id not in camera_ids:
                camera_ids.append(camera_id)

        return camera_ids

    def get_latest_tracking(self, camera_id=None, count=20):
        messages = self.redis.xrevrange("tracked_objects", count=count)

        for _, msg in messages:
            payload = json.loads(msg["payload"])

            if camera_id is None or payload.get("camera_id") == camera_id:
                return payload

        return None

    def get_latest_events(self, camera_id=None, count=20):
        events = self.redis.xrevrange("ui_events", count=count)
        parsed = []

        for msg_id, data in events:
            payload = json.loads(data["payload"])

            if camera_id is not None and payload.get("camera_id") != camera_id:
                continue

            payload["redis_id"] = msg_id
            parsed.append(payload)

        return parsed

    def get_plate_lookup(self, track_ids):
        plate_lookup = {}

        for track_id in track_ids:
            plate = self.redis.get(f"plate:{track_id}")

            if plate:
                plate_lookup[track_id] = plate

        return plate_lookup
