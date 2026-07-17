import subprocess
import sys
import time
from pathlib import Path

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError


ROOT = Path(__file__).resolve().parents[1]
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPICS = [
    ("vision_detections", 1, 1, None),
    ("tracked_objects", 1, 1, None),
    ("plate_events", 1, 1, None),
    ("vehicle_identity", 1, 1, None),
    ("ui_events", 1, 1, None),
    ("vehicle_plate_cache", 1, 1, {"cleanup.policy": "compact"}),
]


def init_kafka():
    admin = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        client_id="traffic-pipeline-init",
    )
    try:
        for name, partitions, replication_factor, config in TOPICS:
            topic = NewTopic(
                name=name,
                num_partitions=partitions,
                replication_factor=replication_factor,
                topic_configs=config,
            )
            try:
                admin.create_topics([topic], validate_only=False)
                print(f"Kafka topic created: {name}")
            except TopicAlreadyExistsError:
                print(f"Kafka topic already exists: {name}")
    finally:
        admin.close()


def start_service(relative_path):
    path = ROOT / relative_path
    return subprocess.Popen([sys.executable, str(path)], cwd=str(path.parent))


if __name__ == "__main__":
    print("Initializing Kafka topics...")
    init_kafka()

    print("Starting services...")

    vision = start_service("vision_service/main.py")
    time.sleep(3)

    tracking = start_service("tracking_service/main.py")
    time.sleep(2)

    plate = start_service("plate_service/main.py")
    event = start_service("event_service/main.py")
    graph = start_service("graph_service/main.py")

    print("Services started")
    print("Starting UI")

    ui_path = ROOT.parent / "ui" / "app.py"
    ui = subprocess.Popen(["streamlit", "run", str(ui_path)])

    vision.wait()
    tracking.wait()
    plate.wait()
    event.wait()
    graph.wait()
    ui.wait()
