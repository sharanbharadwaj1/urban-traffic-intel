import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from kafka_common import KafkaJsonConsumer


class StreamReader:

    def __init__(self, bootstrap_servers, stream):

        self.stream = stream
        self.kafka = KafkaJsonConsumer(
            bootstrap_servers=bootstrap_servers,
            topic=stream,
            group_id="event_service",
        )

    def read(self):

        for data in self.kafka.read():
            yield data
