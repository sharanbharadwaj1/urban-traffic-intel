import redis
import json


class StreamReader:

    def __init__(self, host, port, stream):

        self.redis = redis.Redis(host=host, port=port)
        self.stream = stream
        self.group = "tracking_group"
        self.consumer = "tracker_1"

    def read(self):

        while True:

            response = self.redis.xreadgroup(
                groupname=self.group,
                consumername=self.consumer,
                streams={self.stream: ">"},
                block=0
            )

            for stream, messages in response:

                for msg_id, msg in messages:

                    data = json.loads(msg[b'payload'])

                    yield msg_id, data


# import redis
# import json

# class StreamReader:

#     def __init__(self, host, port, stream):

#         self.redis = redis.Redis(host=host, port=port)
#         self.stream = stream
#         self.last_id = "0"

#     def read(self):

#         response = self.redis.xread(
#             {self.stream: self.last_id},
#             block=0
#         )

#         for stream, messages in response:

#             for msg_id, msg in messages:

#                 self.last_id = msg_id

#                 data = json.loads(msg[b'payload'])

#                 yield data