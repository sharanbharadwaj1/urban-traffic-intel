import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from kafka_common import TrackHistoryStore


class TrackStore:

    def __init__(self, max_history, ttl):

        self.store = TrackHistoryStore(max_history, ttl)

    def update_track(self, camera_id, obj, frame_id):

        self.store.update_track(camera_id, obj, frame_id)

    def get_track_history(self, camera_id, track_id):

        return self.store.get_track_history(camera_id, track_id)
