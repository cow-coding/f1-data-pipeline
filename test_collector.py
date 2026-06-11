import json
import random
from datetime import datetime, UTC

import requests

COLLECTOR_URL = "http://localhost:8000/events"

FAKE_EVENTS = {
    "car_data": {
        "driver_number": 1,
        "speed": 312,
        "rpm": 11800,
        "gear": 8,
        "throttle": 99,
        "brake": 0,
        "drs": 12,
        "session_key": 9158,
    },
    "position": {
        "driver_number": 16,
        "x": 1234,
        "y": 5678,
        "z": 0,
        "session_key": 9158,
    },
    "pit": {
        "driver_number": 44,
        "lap_number": 23,
        "pit_duration": 2.4,
        "session_key": 9158,
    },
    "weather": {
        "air_temperature": 31.2,
        "track_temperature": 44.8,
        "humidity": 58,
        "wind_speed": 1.2,
        "rainfall": 0,
        "session_key": 9158,
    },
    "race_control": {
        "message": "TRACK CLEAR",
        "flag": "GREEN",
        "lap_number": 10,
        "session_key": 9158,
    },
}


def make_event(event_type: str) -> dict:
    return {
        "event_type": event_type,
        "emitted_at": datetime.now(UTC).isoformat(),
        "payload": FAKE_EVENTS[event_type],
    }


def send(n: int = 15) -> None:
    print(f"sending {n} events to {COLLECTOR_URL}\n")
    event_types = list(FAKE_EVENTS.keys())

    for i in range(n):
        event_type = random.choice(event_types)
        body = make_event(event_type)

        try:
            resp = requests.post(COLLECTOR_URL, json=body, timeout=5)
            print(f"[{i+1:02d}] event_type={event_type} status={resp.status_code}")
        except requests.RequestException as e:
            print(f"[{i+1:02d}] FAILED event_type={event_type} error={e}")

    print("\ndone. check collector/data/ for parquet files.")


if __name__ == "__main__":
    send(n=15)
