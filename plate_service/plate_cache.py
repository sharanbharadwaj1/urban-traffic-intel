import redis


class PlateCache:

    def __init__(self, host, port):

        self.redis = redis.Redis(host=host, port=port)

    def get_plate(self, track_id):

        key = f"plate:{track_id}"

        value = self.redis.get(key)

        if value:
            return value.decode()

        return None

    def set_plate(self, track_id, plate):

        key = f"plate:{track_id}"

        self.redis.set(key, plate)