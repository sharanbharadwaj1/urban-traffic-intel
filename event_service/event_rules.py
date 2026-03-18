from motion import estimate_speed



def detect_congestion(objects):

    vehicle_count = len(objects)

    if vehicle_count > 15:

        return {
            "event_type": "traffic_congestion",
            "vehicle_count": vehicle_count
        }

    return None



def detect_stopped_vehicle(history):

    speed = estimate_speed(history)

    if speed < 2:

        return {
            "event_type": "vehicle_stopped",
            "speed": speed
        }

    return None

def detect_speeding_vehicle(history):

    speed = estimate_speed(history)

    if speed > 60:

        return {
            "event_type": "vehicle_speeding",
            "speed": speed
        }

    return None