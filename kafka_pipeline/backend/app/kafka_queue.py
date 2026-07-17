import json
import uuid

from kafka import KafkaConsumer, KafkaProducer


class KafkaJobQueue:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda value: str(value).encode("utf-8") if value else None,
            retries=5,
        )

    def enqueue(self, job_id: str) -> str:
        queue_task_id = uuid.uuid4().hex
        self.producer.send(
            self.topic,
            key=job_id,
            value={"task_id": queue_task_id, "job_id": job_id},
        )
        self.producer.flush()
        return queue_task_id


def consume_jobs(bootstrap_servers: str, topic: str, group_id: str):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )
    for record in consumer:
        yield record.value, consumer
