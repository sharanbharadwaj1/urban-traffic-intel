from stream_reader import StreamReader
from tracker import Tracker
from publisher import Publisher
import config


reader = StreamReader(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.INPUT_STREAM
)

tracker = Tracker()

publisher = Publisher(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.OUTPUT_STREAM
)

for msg_id, message in reader.read():

    detections = message["detections"]

    objects = tracker.update(detections, message["frame_id"])

    event = {
        "camera_id": message["camera_id"],
        "frame_id": message["frame_id"],
        "frame": message["frame"],
        "objects": objects
    }

    publisher.publish(event)

    reader.redis.xack(
        config.INPUT_STREAM,
        "tracking_group",
        msg_id
    )

    print("Processed frame", message["frame_id"])




# from stream_reader import StreamReader
# from tracker import Tracker
# from publisher import Publisher
# import config

# reader = StreamReader(
#     config.REDIS_HOST,
#     config.REDIS_PORT,
#     config.INPUT_STREAM
# )

# tracker = Tracker()

# publisher = Publisher(
#     config.REDIS_HOST,
#     config.REDIS_PORT,
#     config.OUTPUT_STREAM
# )

# for message in reader.read():

#     detections = message["detections"]

#     tracks = tracker.update(detections)

#     publisher.publish({
#         "frame_id": message["frame_id"],
#         "tracks": str(tracks)
#     })
