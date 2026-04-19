from frame_source import FrameSource
from detector import Detector
from publisher import Publisher
import config
import time
import sys
import base64
import cv2
import sys

if len(sys.argv) > 1:
    camera_id = sys.argv[1]
else:
    camera_id = "cam_1"

source = FrameSource(config.VIDEO_SOURCE)

detector = Detector(config.MODEL_NAME)

publisher = Publisher(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.STREAM_NAME
)

frame_id = 0

while True:

    frame = source.read()

    if frame is None:
        break

    frame_id += 1

    detections = detector.detect(frame)
    _, buffer = cv2.imencode(".jpg", frame)

    frame_base64 = base64.b64encode(buffer).decode("utf-8")
    message = {
        "camera_id": camera_id,
        "frame_id": frame_id,
        "timestamp": time.time(),
        "detections": detections,
        "frame": frame_base64
    }

    publisher.publish(message)

    print(f"Published frame {frame_id}")


