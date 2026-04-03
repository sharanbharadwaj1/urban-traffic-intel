import os
from datetime import timezone

from neo4j import GraphDatabase


class GraphReader:

    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def get_camera_sightings(self, camera_id, limit=20):
        query = """
        MATCH (v:Vehicle)-[r:SEEN_AT]->(c:Camera {id: $camera_id})
        RETURN
            v.plate AS plate,
            c.id AS camera_id,
            r.first_seen_at AS first_seen_at,
            r.last_seen_at AS last_seen_at,
            r.total_sightings AS total_sightings
        ORDER BY r.last_seen_at DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            results = session.run(query, camera_id=camera_id, limit=limit)
            rows = []
            for record in results:
                rows.append(
                    {
                        "plate": record["plate"],
                        "camera_id": record["camera_id"],
                        "first_seen_at": self._to_gmt_string(record["first_seen_at"]),
                        "last_seen_at": self._to_gmt_string(record["last_seen_at"]),
                        "total_sightings": record["total_sightings"],
                    }
                )
            return rows

    @staticmethod
    def _to_gmt_string(value):
        if value is None:
            return ""

        native = value.to_native() if hasattr(value, "to_native") else value
        native = native.astimezone(timezone.utc)
        return native.strftime("%Y-%m-%d %H:%M:%S GMT")
