from neo4j import GraphDatabase


class GraphWriter:

    def __init__(self, uri, user, password):

        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._ensure_constraints()

    def _ensure_constraints(self):
        with self.driver.session() as session:
            session.run(
                """
                CREATE CONSTRAINT vehicle_plate_unique IF NOT EXISTS
                FOR (v:Vehicle) REQUIRE v.plate IS UNIQUE
                """
            )
            session.run(
                """
                CREATE CONSTRAINT camera_id_unique IF NOT EXISTS
                FOR (c:Camera) REQUIRE c.id IS UNIQUE
                """
            )

    def write_vehicle_camera(self, plate, camera_id, track_id=None):

        query = """
        MERGE (v:Vehicle {plate:$plate})
        MERGE (c:Camera {id:$camera})
        MERGE (v)-[r:SEEN_AT]->(c)
        ON CREATE SET
            r.first_seen_at = datetime(),
            r.first_track_id = $track_id
        SET
            r.last_seen_at = datetime(),
            r.last_track_id = $track_id
        """

        with self.driver.session() as session:
            session.run(
                query,
                plate=plate,
                camera=camera_id,
                track_id=track_id,
            )
