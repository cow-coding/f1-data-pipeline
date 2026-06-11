import time
import random
import logging
import requests
from datetime import datetime

from config import (
    OPENF1_BASE_URL,
    COLLECTOR_URL,
    DEFAULT_SESSION_KEY,
    EMIT_INTERVAL_SEC,
    ENDPOINTS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_openf1(endpoint: str, session_key: int) -> list[dict]:
    url = f"{OPENF1_BASE_URL}/{endpoint}"
    params = {"session_key": session_key}

    # car_data/position는 데이터가 너무 많아서 드라이버 1명치만 샘플링
    if endpoint in ("car_data", "position"):
        params["driver_number"] = random.choice([1, 11, 16, 44, 55, 63])

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def emit(event_type: str, payload: dict) -> None:
    body = {
        "event_type": event_type,
        "emitted_at": datetime.utcnow().isoformat(),
        "payload": payload,
    }
    try:
        resp = requests.post(COLLECTOR_URL, json=body, timeout=5)
        resp.raise_for_status()
        logger.info("emitted event_type=%s status=%s", event_type, resp.status_code)
    except requests.RequestException as e:
        logger.warning("failed to emit event_type=%s error=%s", event_type, e)


def run(session_key: int = DEFAULT_SESSION_KEY) -> None:
    logger.info("fetching data for session_key=%s", session_key)

    # 세션 시작 시 각 엔드포인트 데이터를 미리 가져와서 메모리에 보관
    data_pool: dict[str, list[dict]] = {}
    for endpoint in ENDPOINTS:
        try:
            records = fetch_openf1(endpoint, session_key)
            data_pool[endpoint] = records
            logger.info("loaded endpoint=%s records=%d", endpoint, len(records))
        except Exception as e:
            logger.warning("failed to load endpoint=%s error=%s", endpoint, e)
            data_pool[endpoint] = []

    logger.info("starting event emission loop")
    while True:
        # 데이터가 있는 엔드포인트 중 랜덤 선택
        available = [ep for ep, rows in data_pool.items() if rows]
        if not available:
            logger.error("no data available, exiting")
            break

        endpoint = random.choice(available)
        record = random.choice(data_pool[endpoint])
        emit(event_type=endpoint, payload=record)

        time.sleep(EMIT_INTERVAL_SEC)


if __name__ == "__main__":
    run()
