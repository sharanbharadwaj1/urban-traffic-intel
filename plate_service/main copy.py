from stream_reader import StreamReader
from plate_cache import PlateCache
from ocr_reader import OCRReader
from plate_detector import crop_vehicle,detect_plate
import config
import redis

reader = StreamReader(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.INPUT_STREAM
)


cache = PlateCache(
    config.REDIS_HOST,
    config.REDIS_PORT
)

ocr = OCRReader()


for message in reader.read():

    objects = message["objects"]

    frame = None   # later we can pass frame if available

    for obj in objects:

        track_id = obj["track_id"]

        plate = cache.get_plate(track_id)

        if plate:
            continue

        plate = detect_plate(frame, obj["bbox"])

        if plate:

            redis.set(f"plate:{track_id}", plate)

            print("Plate detected:", plate)
        # here we would crop vehicle frame
        # placeholder since frames are not passed yet
        plate_text = plate

        if plate_text:

            cache.set_plate(track_id, plate_text)

            print("Plate detected:", plate_text)