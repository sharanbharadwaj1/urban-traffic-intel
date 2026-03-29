from ocr_reader import OCRReader


ocr_reader = OCRReader()


def crop_vehicle(frame, bbox):

    x1, y1, x2, y2 = map(int, bbox)

    return frame[y1:y2, x1:x2]

def detect_plate(frame, bbox):

    vehicle = crop_vehicle(frame, bbox)

    if vehicle.size == 0:
        return None

    return ocr_reader.read_plate(vehicle)
