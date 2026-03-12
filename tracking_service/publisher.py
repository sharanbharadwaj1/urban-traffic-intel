import redis
import json

class Publisher:

    def __init__(self, host, port, stream_name):

        self.redis = redis.Redis(host=host, port=port)
        self.stream_name = stream_name

    def publish(self, data):

        self.redis.xadd(
            self.stream_name,
            {"payload": json.dumps(data)}
        )