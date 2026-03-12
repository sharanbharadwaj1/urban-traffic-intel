from frame_reader import FrameReader
from detector import Detector
from publisher import Publisher
import config
import time
import sys

camera_id = sys.argv[1]

reader = FrameReader(config.VIDEO_SOURCE, config.FRAME_SKIP)

detector = Detector(config.MODEL_NAME)

publisher = Publisher(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.STREAM_NAME
)

for frame_id, frame in reader.read():

    detections = detector.detect(frame)

    message = {
        "camera_id": camera_id,
        "frame_id": frame_id,
        "timestamp": time.time(),
        "detections": detections
    }

    publisher.publish(message)

    print("Published frame", frame_id)