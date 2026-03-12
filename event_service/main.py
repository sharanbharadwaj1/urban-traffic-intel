from stream_reader import StreamReader
from track_store import TrackStore
from event_rules import detect_congestion
import config


reader = StreamReader(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.INPUT_STREAM
)

store = TrackStore(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.MAX_TRACK_HISTORY,
    config.TRACK_TTL
)

for message in reader.read():

    camera_id = message["camera_id"]
    frame_id = message["frame_id"]
    objects = message["objects"]

    for obj in objects:

        store.update_track(camera_id, obj, frame_id)

    event = detect_congestion(objects)

    if event:

        print("EVENT DETECTED:", event)