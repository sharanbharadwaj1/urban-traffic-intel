import os


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

INPUT_STREAM = os.getenv("PLATE_INPUT_STREAM", "plate_events")
OUTPUT_STREAM = os.getenv("PLATE_OUTPUT_STREAM", "vehicle_identity")

PLATE_CONFIRMATION_READS = 1
PLATE_MIN_LENGTH = 7
PLATE_MAX_LENGTH = 11
PLATE_MAX_CANDIDATES = 4
PLATE_TRACK_BUFFER_SIZE = 6
PLATE_TRACK_PROCESS_TOP_K = 1
PLATE_TRACK_MAX_ATTEMPTS = 12
PLATE_TRACK_TTL_FRAMES = 90
PLATE_RETRY_COOLDOWN_FRAMES = int(os.getenv("PLATE_RETRY_COOLDOWN_FRAMES", "20"))
ANPR_PROVIDER = os.getenv("ANPR_PROVIDER", "plate_recognizer")
ANPR_API_URL = os.getenv("ANPR_API_URL", "https://api.platerecognizer.com/v1/plate-reader/")
ANPR_API_TOKEN = os.getenv("ANPR_API_TOKEN", os.getenv("PLATE_RECOGNIZER_API_TOKEN", "f27d131868069151c84f1f7fcea4412a47267412"))
ANPR_COUNTRY = os.getenv("ANPR_COUNTRY", "in")
ANPR_MIN_SCORE = float(os.getenv("ANPR_MIN_SCORE", "0.5"))
ANPR_TIMEOUT_SECONDS = int(os.getenv("ANPR_TIMEOUT_SECONDS", "15"))
ANPR_MIN_INTERVAL_SECONDS = float(os.getenv("ANPR_MIN_INTERVAL_SECONDS", "2.0"))
ANPR_RETRY_BACKOFF_SECONDS = float(os.getenv("ANPR_RETRY_BACKOFF_SECONDS", "5.0"))
PLATE_DEBUG = os.getenv("PLATE_DEBUG", "false").lower() == "true"
PLATE_DEBUG_DIR = os.getenv("PLATE_DEBUG_DIR", "debug_plate")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "trafficdb1")
POSTGRES_USER = os.getenv("POSTGRES_USER", "traffic1")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "traffic1")
