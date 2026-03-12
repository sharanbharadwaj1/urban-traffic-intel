def detect_congestion(objects):

    vehicle_count = len(objects)

    if vehicle_count > 15:

        return {
            "event_type": "traffic_congestion",
            "vehicle_count": vehicle_count
        }

    return None