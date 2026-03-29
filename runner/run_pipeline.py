import subprocess
import time
import redis
import sys

REDIS_HOST = "localhost"
REDIS_PORT = 6379

VISION_STREAM = "vision_detections"
TRACKING_GROUP = "tracking_group"


def init_redis():

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

    try:
        r.xgroup_create(
            name=VISION_STREAM,
            groupname=TRACKING_GROUP,
            id="0",
            mkstream=True
        )
        print("Consumer group created")

    except Exception:
        print("Consumer group already exists")


def start_service(path):

    return subprocess.Popen([sys.executable, path])


if __name__ == "__main__":

    print("Initializing Redis streams...")
    init_redis()

    print("Starting services...")

    vision = start_service("../vision_service/main.py")
    time.sleep(3)

    tracking = start_service("../tracking_service/main.py")
    time.sleep(2)

    plate = start_service("../plate_service/main.py")
    event = start_service("../event_service/main.py")
    graph = start_service("../graph_service/main.py")

    print("Services started")

    print("Starting UI")

    ui = subprocess.Popen(["streamlit", "run", "../ui/app.py"])

    vision.wait()
    tracking.wait()
    plate.wait()
    event.wait()
    graph.wait()
    ui.wait()
