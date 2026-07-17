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
            session.run(
                """
                CREATE CONSTRAINT sighting_id_unique IF NOT EXISTS
                FOR (s:Sighting) REQUIRE s.id IS UNIQUE
                """
            )

    def write_vehicle_sighting(
        self,
        plate,
        camera_id,
        track_id=None,
        frame_id=None,
        class_id=None,
        confidence=None,
    ):
        sighting_id = f"{camera_id}:{plate}:{track_id}"
        query = """
        MERGE (v:Vehicle {plate:$plate})
        MERGE (c:Camera {id:$camera})
        MERGE (s:Sighting {id:$sighting_id})
        ON CREATE SET
            s.track_id = $track_id,
            s.first_frame_id = $frame_id,
            s.last_frame_id = $frame_id,
            s.frames_seen = 1,
            s.first_seen_at = datetime(),
            s.last_seen_at = datetime(),
            s.class_id = $class_id,
            s.max_confidence = $confidence
        SET
            s.last_frame_id = $frame_id,
            s.last_seen_at = datetime(),
            s.frames_seen = CASE
                WHEN s.first_seen_at = s.last_seen_at AND s.first_frame_id = $frame_id THEN s.frames_seen
                ELSE coalesce(s.frames_seen, 0) + 1
            END,
            s.class_id = coalesce(s.class_id, $class_id),
            s.max_confidence = CASE
                WHEN s.max_confidence IS NULL OR $confidence > s.max_confidence
                THEN $confidence
                ELSE s.max_confidence
            END
        MERGE (v)-[:OBSERVED_AS]->(s)
        MERGE (s)-[:AT_CAMERA]->(c)
        MERGE (v)-[r:SEEN_AT]->(c)
        ON CREATE SET
            r.first_seen_at = datetime(),
            r.first_frame_id = $frame_id,
            r.first_track_id = $track_id,
            r.total_sightings = 1
        SET
            r.last_seen_at = datetime(),
            r.last_frame_id = $frame_id,
            r.last_track_id = $track_id,
            r.total_sightings = CASE
                WHEN r.first_seen_at = r.last_seen_at AND r.first_frame_id = $frame_id THEN r.total_sightings
                ELSE coalesce(r.total_sightings, 0) + 1
            END
        """

        with self.driver.session() as session:
            session.run(
                query,
                plate=plate,
                camera=camera_id,
                sighting_id=sighting_id,
                track_id=track_id,
                frame_id=frame_id,
                class_id=class_id,
                confidence=confidence,
            )
