from stream_reader import StreamReader
from graph_writer import GraphWriter
import config


reader = StreamReader(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.INPUT_STREAM
)

graph = GraphWriter(
    config.NEO4J_URI,
    config.NEO4J_USER,
    config.NEO4J_PASSWORD
)

for message in reader.read():

    camera_id = message["camera_id"]

    for obj in message["objects"]:

        track_id = obj["track_id"]

        plate = None  # later retrieved from Redis plate cache

        if plate:

            graph.write_vehicle_camera(plate, camera_id)