import psycopg2


class DBWriter:

    def __init__(self):

        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="trafficdb1",
            user="traffic1",
            password="traffic1"
        )

        self.cursor = self.conn.cursor()

    def insert_event(self, camera_id, track_id, event_type):

        query = """
        INSERT INTO events (camera_id, track_id, event_type)
        VALUES (%s, %s, %s)
        """

        self.cursor.execute(query, (camera_id, track_id, event_type))
        self.conn.commit()