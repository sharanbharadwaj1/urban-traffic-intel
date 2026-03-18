from neo4j import GraphDatabase


class GraphWriter:

    def __init__(self, uri, user, password):

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def write_vehicle_camera(self, plate, camera_id):

        query = """
        MERGE (v:Vehicle {plate:$plate})
        MERGE (c:Camera {id:$camera})
        MERGE (v)-[:SEEN_AT]->(c)
        """

        with self.driver.session() as session:
            session.run(query, plate=plate, camera=camera_id)