import json
import threading
import time
import uuid
from collections import OrderedDict
from typing import Any

from kafka import KafkaConsumer, KafkaProducer


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "tolist"):
        return value.tolist()
    return str(value)


class KafkaJsonProducer:
    def __init__(self, bootstrap_servers: str):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value, default=_json_default).encode("utf-8"),
            key_serializer=lambda value: str(value).encode("utf-8") if value is not None else None,
            linger_ms=10,
            retries=5,
        )

    def publish(self, topic: str, data: dict, key: str | None = None) -> None:
        self.producer.send(topic, value=data, key=key)
        self.producer.flush()


class KafkaJsonConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        auto_offset_reset: str = "latest",
    ):
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            key_deserializer=lambda value: value.decode("utf-8") if value else None,
        )

    def read(self):
        for record in self.consumer:
            yield record.value


class TTLSet:
    def __init__(self):
        self.values: dict[str, float] = {}

    def exists(self, key: str) -> bool:
        expires_at = self.values.get(key)
        if expires_at is None:
            return False
        if expires_at <= time.time():
            self.values.pop(key, None)
            return False
        return True

    def set(self, key: str, ttl_seconds: float) -> None:
        self.values[key] = time.time() + ttl_seconds


class TrackHistoryStore:
    def __init__(self, max_history: int, ttl_seconds: float):
        self.max_history = max_history
        self.ttl_seconds = ttl_seconds
        self.history: dict[str, tuple[float, OrderedDict[int, dict]]] = {}

    def update_track(self, camera_id: str, obj: dict, frame_id: int) -> None:
        key = f"{camera_id}:{obj['track_id']}"
        expires_at, entries = self.history.get(key, (0, OrderedDict()))
        entries[frame_id] = {
            "frame": frame_id,
            "bbox": obj["bbox"],
            "confidence": obj["confidence"],
        }
        while len(entries) > self.max_history:
            entries.popitem(last=False)
        self.history[key] = (time.time() + self.ttl_seconds, entries)

    def get_track_history(self, camera_id: str, track_id: str | int) -> list[dict]:
        key = f"{camera_id}:{track_id}"
        expires_at, entries = self.history.get(key, (0, OrderedDict()))
        if expires_at <= time.time():
            self.history.pop(key, None)
            return []
        return list(reversed(entries.values()))


class CompactedTopicStore:
    def __init__(self, bootstrap_servers: str, topic: str, group_prefix: str):
        self.topic = topic
        self.producer = KafkaJsonProducer(bootstrap_servers)
        self.values: dict[str, Any] = {}
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=f"{group_prefix}-{uuid.uuid4().hex}",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")) if value else None,
            key_deserializer=lambda value: value.decode("utf-8") if value else None,
        )
        self.thread = threading.Thread(target=self._consume, daemon=True)
        self.thread.start()

    def _consume(self) -> None:
        for record in self.consumer:
            if record.key is None:
                continue
            if record.value is None:
                self.values.pop(record.key, None)
            else:
                self.values[record.key] = record.value

    def get(self, key: str) -> Any:
        return self.values.get(key)

    def set(self, key: str, value: Any) -> None:
        self.values[key] = value
        self.producer.publish(self.topic, value, key=key)
