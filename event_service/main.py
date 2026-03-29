import redis

import config
from db_writer import DBWriter
from event_rules import (
    detect_congestion,
    detect_speeding_vehicle,
    detect_stopped_vehicle,
)
from publisher import Publisher
from stream_reader import StreamReader
from track_store import TrackStore


redis_client = redis.StrictRedis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    decode_responses=True,
)

event_stream_publisher = Publisher(
    config.REDIS_HOST,
    config.REDIS_PORT,
    "ui_events",
)

plate_publisher = Publisher(
    config.REDIS_HOST,
    config.REDIS_PORT,
    "plate_events",
)

db = DBWriter()

reader = StreamReader(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.INPUT_STREAM,
)

store = TrackStore(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.MAX_TRACK_HISTORY,
    config.TRACK_TTL,
)


def publish_vehicle_event(camera_id, frame_id, obj, rule_result, frame):
    event_type = rule_result["event_type"]
    track_id = obj["track_id"]
    plate = redis_client.get(f"plate:{track_id}")
    event_key = f"event:{camera_id}:{track_id}:{event_type}"

    if redis_client.get(event_key):
        return

    event_metadata = {
        "bbox": obj["bbox"],
        "confidence": obj["confidence"],
        "class_id": obj["class_id"],
    }

    for key, value in rule_result.items():
        if key != "event_type":
            event_metadata[key] = value

    db.insert_event(
        camera_id=camera_id,
        track_id=track_id,
        event_type=event_type,
        plate=plate,
        frame_id=frame_id,
        event_metadata=event_metadata,
    )

    event_data = {
        "camera_id": camera_id,
        "track_id": track_id,
        "event_type": event_type,
        "frame_id": frame_id,
        "plate": plate,
        **event_metadata,
    }
    event_stream_publisher.publish(event_data)

    if plate is None:
        plate_publisher.publish(
            {
                "camera_id": camera_id,
                "track_id": track_id,
                "event_type": event_type,
                "frame": frame,
                "bbox": obj["bbox"],
            }
        )

    redis_client.set(event_key, 1, ex=5)


for message in reader.read():
    camera_id = message["camera_id"]
    frame_id = message["frame_id"]
    objects = message["objects"]

    for obj in objects:
        track_id = obj["track_id"]

        store.update_track(camera_id, obj, frame_id)
        history = store.get_track_history(camera_id, track_id)

        stopped_event = detect_stopped_vehicle(history)
        if stopped_event:
            publish_vehicle_event(
                camera_id,
                frame_id,
                obj,
                stopped_event,
                message["frame"],
            )

        speeding_event = detect_speeding_vehicle(history)
        if speeding_event:
            publish_vehicle_event(
                camera_id,
                frame_id,
                obj,
                speeding_event,
                message["frame"],
            )

    congestion_event = detect_congestion(objects)
    if congestion_event:
        db.insert_event(
            camera_id=camera_id,
            track_id=None,
            event_type=congestion_event["event_type"],
            plate=None,
            frame_id=frame_id,
            event_metadata={
                "vehicle_count": congestion_event["vehicle_count"],
            },
        )
        event_stream_publisher.publish(
            {
                "camera_id": camera_id,
                "track_id": None,
                "event_type": congestion_event["event_type"],
                "frame_id": frame_id,
                "vehicle_count": congestion_event["vehicle_count"],
            }
        )
