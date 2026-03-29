import redis

import config
from graph_writer import GraphWriter
from stream_reader import StreamReader


reader = StreamReader(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.INPUT_STREAM,
)

graph = GraphWriter(
    config.NEO4J_URI,
    config.NEO4J_USER,
    config.NEO4J_PASSWORD,
)

redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    decode_responses=True,
)


for message in reader.read():
    camera_id = message["camera_id"]

    for obj in message["objects"]:
        track_id = obj["track_id"]
        plate = redis_client.get(f"plate:{track_id}")

        if not plate:
            continue

        graph.write_vehicle_camera(
            plate=plate,
            camera_id=camera_id,
            track_id=track_id,
        )
