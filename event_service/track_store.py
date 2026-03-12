import redis
import json


class TrackStore:

    def __init__(self, host, port, max_history, ttl):

        self.redis = redis.Redis(host=host, port=port)
        self.max_history = max_history
        self.ttl = ttl

    def update_track(self, camera_id, obj, frame_id):

        key = f"track:{camera_id}:{obj['track_id']}"

        entry = {
            "frame": frame_id,
            "bbox": obj["bbox"],
            "confidence": obj["confidence"]
        }

        self.redis.lpush(key, json.dumps(entry))

        self.redis.ltrim(key, 0, self.max_history)

        self.redis.expire(key, self.ttl)

    def get_track_history(self, camera_id, track_id):

        key = f"track:{camera_id}:{track_id}"

        history = self.redis.lrange(key, 0, -1)

        return [json.loads(h) for h in history]