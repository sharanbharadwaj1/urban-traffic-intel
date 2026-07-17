import json

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from kafka_common import KafkaJsonProducer


class Publisher:

    def __init__(self, bootstrap_servers, stream_name):
        self.kafka = KafkaJsonProducer(bootstrap_servers)
        self.stream_name = stream_name

    def publish(self, data):
        self.kafka.publish(self.stream_name, data, key=data.get("track_id"))
