import redis
import json


class RedisReader:

    def __init__(self):

        self.redis = redis.Redis(host="localhost", port=6379)

    def get_latest_tracking(self):

        messages = self.redis.xrevrange("tracked_objects", count=1)

        if not messages:
            return None

        _, msg = messages[0]

        return json.loads(msg[b'payload'])