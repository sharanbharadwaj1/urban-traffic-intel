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


for message in reader.read():
    camera_id = message["camera_id"]
    frame_id = message.get("frame_id")
    graph.write_vehicle_sighting(
        plate=message["plate"],
        camera_id=camera_id,
        track_id=message.get("track_id"),
        frame_id=frame_id,
        class_id=message.get("class_id"),
        confidence=message.get("confidence"),
    )
