import math

def bbox_center(bbox):

    x1, y1, x2, y2 = bbox

    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    return cx, cy


def pixel_distance(b1, b2):

    x1, y1 = bbox_center(b1)
    x2, y2 = bbox_center(b2)

    return math.sqrt((x2-x1)**2 + (y2-y1)**2)
    
def estimate_speed(history, fps=30):

    if len(history) < 2:
        return 0

    first = history[-1]
    last = history[0]

    dist = pixel_distance(first["bbox"], last["bbox"])

    frame_diff = last["frame"] - first["frame"]

    time = frame_diff / fps

    if time == 0:
        return 0

    return dist / time