import config
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from kafka_common import CompactedTopicStore, TTLSet
from db_writer import DBWriter
from event_rules import (
    detect_congestion,
    detect_speeding_vehicle,
    detect_stopped_vehicle,
)
from motion import estimate_speed
from publisher import Publisher
from stream_reader import StreamReader
from track_store import TrackStore


plate_cache = CompactedTopicStore(
    config.KAFKA_BOOTSTRAP_SERVERS,
    config.PLATE_CACHE_TOPIC,
    "event-plate-cache",
)
event_dedupe = TTLSet()
plate_request_dedupe = TTLSet()

event_stream_publisher = Publisher(
    config.KAFKA_BOOTSTRAP_SERVERS,
    "ui_events",
)

plate_publisher = Publisher(
    config.KAFKA_BOOTSTRAP_SERVERS,
    "plate_events",
)

db = DBWriter()

reader = StreamReader(
    config.KAFKA_BOOTSTRAP_SERVERS,
    config.INPUT_STREAM,
)

store = TrackStore(
    config.MAX_TRACK_HISTORY,
    config.TRACK_TTL,
)

PLATE_ELIGIBLE_CLASS_IDS = {2, 5, 7}


def publish_vehicle_event(camera_id, frame_id, obj, rule_result):
    event_type = rule_result["event_type"]
    track_id = obj["track_id"]
    plate = plate_cache.get(f"plate:{track_id}")
    event_key = f"event:{camera_id}:{track_id}:{event_type}"

    if event_dedupe.exists(event_key):
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

    event_stream_publisher.publish(
        {
            "camera_id": camera_id,
            "track_id": track_id,
            "event_type": event_type,
            "frame_id": frame_id,
            "plate": plate,
            **event_metadata,
        }
    )

    event_dedupe.set(event_key, 5)


def should_request_plate(obj, speed):
    if obj["class_id"] not in PLATE_ELIGIBLE_CLASS_IDS:
        return False

    x1, y1, x2, y2 = obj["bbox"]
    width = x2 - x1
    height = y2 - y1

    if width < config.PLATE_MIN_WIDTH or height < config.PLATE_MIN_HEIGHT:
        return False

    return True


def motion_event_type(speed):
    if speed < config.PLATE_MIN_SPEED:
        return "vehicle_stopped"

    return "vehicle_moving"


def publish_plate_request(camera_id, frame_id, obj, frame, speed):
    track_id = obj["track_id"]

    if plate_cache.get(f"plate:{track_id}"):
        return

    request_key = f"plate_request:{camera_id}:{track_id}"
    if plate_request_dedupe.exists(request_key):
        return

    plate_publisher.publish(
        {
            "camera_id": camera_id,
            "track_id": track_id,
            "frame_id": frame_id,
            "event_type": motion_event_type(speed),
            "frame": frame,
            "bbox": obj["bbox"],
            "class_id": obj["class_id"],
            "speed": speed,
        }
    )

    plate_request_dedupe.set(request_key, config.PLATE_REQUEST_TTL)


for message in reader.read():
    camera_id = message["camera_id"]
    frame_id = message["frame_id"]
    objects = message["objects"]

    for obj in objects:
        track_id = obj["track_id"]

        store.update_track(camera_id, obj, frame_id)
        history = store.get_track_history(camera_id, track_id)
        speed = estimate_speed(history)

        if should_request_plate(obj, speed):
            publish_plate_request(
                camera_id,
                frame_id,
                obj,
                message["frame"],
                speed,
            )

        stopped_event = detect_stopped_vehicle(history)
        if stopped_event:
            publish_vehicle_event(
                camera_id,
                frame_id,
                obj,
                stopped_event,
            )

        speeding_event = detect_speeding_vehicle(history)
        if speeding_event:
            publish_vehicle_event(
                camera_id,
                frame_id,
                obj,
                speeding_event,
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
