import re

import config
from anpr_client import ANPRClient


anpr_client = ANPRClient()


def _normalize_plate(text):
    if not text:
        return None

    cleaned = re.sub(r"[^A-Z0-9]", "", str(text).upper())
    if len(cleaned) < config.PLATE_MIN_LENGTH or len(cleaned) > config.PLATE_MAX_LENGTH:
        return None

    letter_count = sum(char.isalpha() for char in cleaned)
    digit_count = sum(char.isdigit() for char in cleaned)
    if letter_count < 2 or digit_count < 2:
        return None

    return cleaned


def detect_plate(frame, bbox):
    plate = anpr_client.read_plate_for_bbox(frame, bbox)
    return _normalize_plate(plate)
