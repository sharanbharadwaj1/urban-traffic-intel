def crop_vehicle(frame, bbox):

    x1, y1, x2, y2 = map(int, bbox)

    return frame[y1:y2, x1:x2]

def detect_plate(frame, bbox):

    x1, y1, x2, y2 = map(int, bbox)

    vehicle = frame[y1:y2, x1:x2]

    results = reader.readtext(vehicle)

    if not results:
        return None

    plate = results[0][1]

    return plate