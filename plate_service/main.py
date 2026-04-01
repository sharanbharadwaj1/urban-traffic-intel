import base64

import cv2
import numpy as np

import config
from db_writer import DBWriter
from plate_cache import PlateCache
from plate_detector import detect_plate
from stream_reader import StreamReader
from track_buffer import TrackSnapshotBuffer


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
pending_reads = {}
attempt_counts = {}
snapshot_buffer = TrackSnapshotBuffer()
next_attempt_frame = {}


for message in reader.read():
    track_id = message["track_id"]
    camera_id = message.get("camera_id")
    frame_id = message.get("frame_id", 0)
    print(f"[plate] received track={track_id} frame={frame_id} event={message.get('event_type')}")

    if cache.get_plate(track_id):
        print(f"[plate] track={track_id} already cached, skipping")
        snapshot_buffer.clear(track_id)
        pending_reads.pop(track_id, None)
        attempt_counts.pop(track_id, None)
        next_attempt_frame.pop(track_id, None)
        continue

    frame_bytes = base64.b64decode(message["frame"])
    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

    if frame is None:
        continue

    bbox = message["bbox"]
    snapshot_buffer.add(
        track_id,
        frame_id,
        frame,
        bbox,
        metadata={
            "camera_id": camera_id,
            "event_type": message.get("event_type"),
            "speed": message.get("speed"),
        },
    )

    expired_tracks = snapshot_buffer.prune(frame_id)
    for expired_track_id in expired_tracks:
        pending_reads.pop(expired_track_id, None)
        attempt_counts.pop(expired_track_id, None)
        next_attempt_frame.pop(expired_track_id, None)

    attempts = attempt_counts.get(track_id, 0)
    if attempts >= config.PLATE_TRACK_MAX_ATTEMPTS:
        print(f"[plate] track={track_id} exceeded attempts, clearing buffer")
        snapshot_buffer.clear(track_id)
        pending_reads.pop(track_id, None)
        attempt_counts.pop(track_id, None)
        next_attempt_frame.pop(track_id, None)
        continue

    retry_at = next_attempt_frame.get(track_id, 0)
    if frame_id < retry_at:
        continue

    plate = None
    snapshots = snapshot_buffer.best(track_id)
    if snapshots:
        snapshot = snapshots[0]
        print(
            f"[plate] trying track={track_id} snapshot_frame={snapshot['frame_id']} "
            f"attempt={attempts + 1}"
        )
        try:
            plate = detect_plate(snapshot["frame"], snapshot["bbox"])
        except Exception as exc:
            print(
                f"[plate] detect error track={track_id} "
                f"snapshot_frame={snapshot['frame_id']} error={exc}"
            )
            plate = None
        if plate:
            print(f"[plate] candidate detected track={track_id} plate={plate}")

    attempt_counts[track_id] = attempts + 1
    next_attempt_frame[track_id] = frame_id + config.PLATE_RETRY_COOLDOWN_FRAMES
    if not plate:
        print(f"[plate] no plate found for track={track_id} on attempt={attempt_counts[track_id]}")

    if plate:
        track_reads = pending_reads.setdefault(track_id, {})
        track_reads[plate] = track_reads.get(plate, 0) + 1
        print(
            f"[plate] confirmation track={track_id} plate={plate} "
            f"count={track_reads[plate]}/{config.PLATE_CONFIRMATION_READS}"
        )

        if track_reads[plate] >= config.PLATE_CONFIRMATION_READS:
            try:
                cache.set_plate(track_id, plate)
                print(f"[plate] cache write ok track={track_id} plate={plate}")
            except Exception as exc:
                print(f"[plate] cache write failed track={track_id} error={exc}")
                raise

            try:
                db.update_plate(track_id, plate, camera_id=camera_id)
                print(f"[plate] db write ok track={track_id} plate={plate}")
            except Exception as exc:
                print(f"[plate] db write failed track={track_id} error={exc}")
                raise
            pending_reads.pop(track_id, None)
            attempt_counts.pop(track_id, None)
            next_attempt_frame.pop(track_id, None)
            snapshot_buffer.clear(track_id)
            print(f"[plate] stored track={track_id} plate={plate}")
