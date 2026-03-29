import base64

import cv2
import numpy as np

import config
from db_writer import DBWriter
from plate_cache import PlateCache
from plate_detector import detect_plate
from stream_reader import StreamReader


db = DBWriter()

reader = StreamReader(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.INPUT_STREAM,
)

cache = PlateCache(
    config.REDIS_HOST,
    config.REDIS_PORT,
)


for message in reader.read():
    track_id = message["track_id"]
    camera_id = message.get("camera_id")

    if cache.get_plate(track_id):
        continue

    frame_bytes = base64.b64decode(message["frame"])
    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

    if frame is None:
        continue

    bbox = message["bbox"]
    plate = detect_plate(frame, bbox)

    if plate:
        cache.set_plate(track_id, plate)
        db.update_plate(track_id, plate, camera_id=camera_id)
        print("Plate detected:", plate)
