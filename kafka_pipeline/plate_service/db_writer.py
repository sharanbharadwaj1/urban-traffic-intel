from pathlib import Path

import psycopg2

import config


class DBWriter:

    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            dbname=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
        self._ensure_schema()

    def _ensure_schema(self):
        schema_path = Path(__file__).resolve().parents[1] / "models" / "schema.sql"

        with schema_path.open("r", encoding="utf-8") as schema_file:
            self.cursor.execute(schema_file.read())

    def update_plate(self, track_id, plate, camera_id=None):
        conditions = [
            "track_id = %s",
            "plate IS NULL",
        ]
        params = [track_id]

        if camera_id is not None:
            conditions.append("camera_id = %s")
            params.append(camera_id)

        query = f"""
        UPDATE events
        SET plate = %s
        WHERE {' AND '.join(conditions)}
        """

        self.cursor.execute(query, [plate, *params])

    def close(self):
        self.cursor.close()
        self.conn.close()
