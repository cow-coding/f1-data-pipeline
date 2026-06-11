import os
from dotenv import load_dotenv

load_dotenv()

OPENF1_BASE_URL = "https://api.openf1.org/v1"
COLLECTOR_URL = os.getenv("COLLECTOR_URL", "http://localhost:8000/events")

# 2024 Bahrain GP - session_key 9158
DEFAULT_SESSION_KEY = int(os.getenv("SESSION_KEY", "9158"))

EMIT_INTERVAL_SEC = float(os.getenv("EMIT_INTERVAL_SEC", "1.0"))

ENDPOINTS = [
    "car_data",
    "position",
    "pit",
    "weather",
    "race_control",
]

# 시작 시 한 번만 로드하는 dimension 엔드포인트
DIM_ENDPOINTS = [
    "drivers",
    "sessions",
]
