from stream_reader import StreamReader
from track_store import TrackStore
from event_rules import detect_congestion, detect_speeding_vehicle, detect_stopped_vehicle
import config
from db_writer import DBWriter

db = DBWriter()


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

        # update Redis track history
        store.update_track(camera_id, obj, frame_id)

        # fetch track history
        history = store.get_track_history(camera_id, obj["track_id"])

        # stopped vehicle detection
        event_stopped_vehicle = detect_stopped_vehicle(history)

        if event_stopped_vehicle:
            # print("EVENT:", event_stopped_vehicle)
            db.insert_event(
            camera_id,
            obj["track_id"],
            "vehicle_stopped"
            )

    # congestion detection runs once per frame
    event_congestion = detect_congestion(objects)

    if event_congestion:
        # print("EVENT DETECTED:", event_congestion)
        db.insert_event(
        camera_id,
        obj["track_id"],
        "vehicle_congestion"
        )

    vehicle_speeding = detect_speeding_vehicle(history)

    if vehicle_speeding:
        # print("EVENT DETECTED:", vehicle_speeding)
        db.insert_event(
            camera_id,
            obj["track_id"],
            "vehicle_speeding"
        )
