import logging

from neo4j import GraphDatabase

from app.core.config import Settings

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._driver = None
        if self.settings.graph_enabled:
            try:
                self._driver = GraphDatabase.driver(
                    self.settings.neo4j_uri,
                    auth=(self.settings.neo4j_user, self.settings.neo4j_password),
                )
                self._ensure_constraints()
            except Exception:
                logger.exception("graph_init_failed")
                self._driver = None

    @property
    def enabled(self) -> bool:
        return self._driver is not None

    def _ensure_constraints(self) -> None:
        if self._driver is None:
            return
        with self._driver.session() as session:
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
        plate: str,
        camera_id: str,
        track_id: int | None = None,
        frame_id: int | None = None,
        class_name: str | None = None,
        confidence: float | None = None,
    ) -> None:
        if self._driver is None:
            return

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
            s.class_name = $class_name,
            s.max_confidence = $confidence
        SET
            s.last_frame_id = $frame_id,
            s.last_seen_at = datetime(),
            s.class_name = coalesce(s.class_name, $class_name),
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
            r.total_sightings = coalesce(r.total_sightings, 0) + 1
        """
        with self._driver.session() as session:
            session.run(
                query,
                plate=plate,
                camera=camera_id,
                sighting_id=sighting_id,
                track_id=track_id,
                frame_id=frame_id,
                class_name=class_name,
                confidence=confidence,
            )
