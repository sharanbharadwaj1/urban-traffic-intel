import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from kafka_common import CompactedTopicStore


class PlateCache:

    def __init__(self, bootstrap_servers, topic):

        self.store = CompactedTopicStore(bootstrap_servers, topic, "plate-cache")

    def get_plate(self, track_id):

        key = f"plate:{track_id}"

        value = self.store.get(key)

        if value:
            return value

        return None

    def set_plate(self, track_id, plate):

        key = f"plate:{track_id}"

        self.store.set(key, plate)
