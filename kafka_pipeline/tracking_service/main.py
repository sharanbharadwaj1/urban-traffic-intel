from stream_reader import StreamReader
from tracker import Tracker
from publisher import Publisher
import config


reader = StreamReader(
    config.KAFKA_BOOTSTRAP_SERVERS,
    config.INPUT_STREAM
)

tracker = Tracker()

publisher = Publisher(
    config.KAFKA_BOOTSTRAP_SERVERS,
    config.OUTPUT_STREAM
)

for message in reader.read():

    detections = message["detections"]

    objects = tracker.update(detections, message["frame_id"])

    event = {
        "camera_id": message["camera_id"],
        "frame_id": message["frame_id"],
        "frame": message["frame"],
        "objects": objects
    }

    publisher.publish(event)

    print("Processed frame", message["frame_id"])
