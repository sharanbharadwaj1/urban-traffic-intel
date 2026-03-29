import json

import redis


class StreamReader:

    def __init__(self, host, port, stream):
        self.redis = redis.Redis(host=host, port=port)
        self.stream = stream
        self.last_id = "0"

    def read(self):
        while True:
            response = self.redis.xread(
                {self.stream: self.last_id},
                block=0,
            )

            for _stream, messages in response:
                for msg_id, msg in messages:
                    self.last_id = msg_id
                    yield json.loads(msg[b"payload"])
