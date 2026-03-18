import cv2


def draw_tracks(frame, objects, plate_lookup=None, speed_lookup=None):

    for obj in objects:

        x1, y1, x2, y2 = map(int, obj["bbox"])
        track_id = obj["track_id"]

        plate = None
        speed = None

        if plate_lookup:
            plate = plate_lookup.get(track_id)

        if speed_lookup:
            speed = speed_lookup.get(track_id)

        label = f"ID {track_id}"

        if speed:
            label += f" | {speed:.1f}px/s"

        if plate:
            label += f" | {plate}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

    return frame