# F1 Data Pipeline

OpenF1 API 데이터를 수집하여 Parquet으로 적재하고, dbt로 star schema 분석 모델을 구축하는 배치 데이터 파이프라인 실습 프로젝트입니다.

## Table of Contents

- [Architecture](#architecture)
- [Data Flow](#data-flow)
- [Components](#components)
  - [Event Generator](#event-generator)
  - [Collector](#collector)
  - [Storage](#storage)
  - [dbt Transform](#dbt-transform)
- [Data Model](#data-model)
- [Getting Started](#getting-started)
- [Tech Stack](#tech-stack)

## Architecture

```
                 ┌───────────────┐
                 │   OpenF1 API  │
                 └───────┬───────┘
                         │ poll + dimension enrich
                 ┌───────▼────────┐
                 │ Event Generator│
                 └───────┬────────┘
                         │ HTTP POST /events
                 ┌───────▼────────┐
                 │   Collector    │  FastAPI + Async Buffer + DLQ
                 └───────┬────────┘
                         │ Parquet flush
                 ┌───────▼────────┐
                 │     MinIO      │  event_type / date / hour 파티셔닝
                 └───────┬────────┘
                         │ read_parquet (DuckDB)
                 ┌───────▼────────┐
                 │      dbt       │  staging → snapshot → fact/dim → mart
                 └───────┬────────┘
                         │
                 ┌───────▼────────┐
                 │   Analytics    │
                 └────────────────┘
```

## Data Flow

1. **Event Generator** 가 OpenF1 API에서 이벤트를 폴링하고, 시작 시 캐싱한 driver/session 정보로 payload를 enrich한 뒤 Collector로 전송합니다.
2. **Collector** 가 이벤트를 받아 전처리(UUID·시간 파생)하고, 버퍼에 모았다가 조건 충족 시 MinIO에 Parquet으로 적재합니다.
3. **MinIO** 에 `event_type / date / hour` Hive 파티션으로 저장됩니다.
4. **dbt** 가 DuckDB로 Parquet을 읽어 staging → snapshot → fact/dim → mart 순으로 변환합니다.

## Components

### Event Generator

OpenF1 API를 폴링하여 Collector로 이벤트를 전송합니다.

- 시작 시 `/v1/drivers`, `/v1/sessions` 를 한 번 캐싱 (정적 dimension)
- 매 이벤트 payload에 `driver_name`, `team_name`, `name_acronym`, `session_name`, `circuit`, `country` 를 병합(enrich)
- `car_data` / `position` 은 데이터량이 많아 드라이버 1명치만 샘플링

### Collector

이벤트 수신 → 전처리 → 버퍼 → MinIO 적재를 담당하는 FastAPI 서버입니다.

| Endpoint | 설명 |
|---|---|
| `POST /events` | 이벤트 수신 후 버퍼에 적재 |
| `GET /health` | 헬스 체크 |

**Buffer 플러시 전략**

- 버퍼에 **100건** 이상 쌓이거나 **시간(hour)이 바뀌면** MinIO에 플러시
- 쓰기 실패 시 **3회 backoff 재시도**
- 최종 실패 시 로컬 **Dead Letter Queue** (JSON) 에 저장 후 다음 플러시 때 재처리

### Storage

MinIO에 Hive 스타일 파티셔닝으로 저장됩니다.

```
s3://f1-raw/raw/
└── event_type=car_data/
    └── date=2023-09-15/
        └── hour=10/
            └── part-{timestamp}-0.parquet
```

수집 대상 5개 엔드포인트:

| event_type | 주요 필드 |
|---|---|
| `car_data` | speed, rpm, n_gear, throttle, brake, drs |
| `position` | x, y, z |
| `pit` | lap_number, pit_duration |
| `weather` | air/track temp, humidity, wind_speed, rainfall |
| `race_control` | message, flag, lap_number |

### dbt Transform

DuckDB를 쿼리 엔진으로 사용하여 Parquet을 변환합니다.

```
models/
├── staging/                    # raw 정제 (JSON 언패킹, 타입 캐스팅) · incremental
│   ├── stg_car_data
│   ├── stg_position_data
│   ├── stg_pit_data
│   ├── stg_weather_data
│   └── stg_race_control_data
└── marts/
    ├── dim/                     # dimension · table
    │   ├── dim_driver           # driver_snapshot 기반 (현재 유효 행)
    │   └── dim_session
    ├── fact/                    # fact · table
    │   └── fact_car_telemetry   # FK + measure + degenerate dim
    └── mart_driver_performance  # fact/dim 소비 집계 마트

snapshots/
└── driver_snapshot             # SCD Type 2 (team/driver 변경 이력 추적)
```

**레이어 책임**

| Layer | 역할 | Materialization |
|---|---|---|
| staging | raw 1:1 정제 (언패킹·캐스팅) | incremental |
| snapshot | dimension 변경 이력 보존 (SCD Type 2) | snapshot |
| dim | 맥락 정보 (누구·어디서) | table |
| fact | 측정값 + dimension FK | table |
| mart | 비즈니스 질문에 답하는 집계 | table |

## Data Model

`mart_driver_performance` 를 중심으로 한 star schema:

```
        dim_driver
            │
            │ driver_number
            ▼
   fact_car_telemetry ──────┐
            ▲               │
            │ session_key   ├──► mart_driver_performance
            │               │
        dim_session         │
                            │
        stg_pit_data ───────┘
```

### dbt Tests

모든 staging 모델에 데이터 품질 테스트가 적용되어 있습니다.

- `not_null` — `event_id`
- `dbt_utils.recency` — `emitted_at` 기준 2시간 이내 데이터 존재 여부 (freshness)

## Getting Started

### 1. 전체 서비스 실행

```bash
docker-compose up --build
```

- MinIO Console: http://localhost:9001 (minioadmin / minioadmin)
- Collector API: http://localhost:8000

### 2. dbt 프로파일 설정

`~/.dbt/profiles.yml` 에 추가합니다.

```yaml
f1_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: dev.duckdb
      s3_endpoint: localhost:9000
      s3_access_key_id: minioadmin
      s3_secret_access_key: minioadmin
      s3_region: us-east-1
      s3_url_style: path
```

### 3. dbt 실행

snapshot이 staging과 dim 사이에 위치하므로 의존성 순서를 자동 정렬하는 `dbt build` 를 권장합니다.

```bash
cd transform/f1_dbt

dbt deps               # 패키지 설치 (최초 1회)
dbt build              # staging → snapshot → fact/dim → mart + test 일괄 실행
```

개별 단계로 실행할 경우 staging → snapshot → 나머지 순서를 지켜야 합니다.

```bash
dbt run --select staging   # 1. staging (snapshot 소스)
dbt snapshot               # 2. snapshot
dbt run                    # 3. dim/fact/mart
dbt test                   # 4. 품질 테스트
```

### 4. 테스트 이벤트 전송

```bash
python test_collector.py
```

## Tech Stack

- **Python** 3.12
- **FastAPI** — Collector API 서버
- **PyArrow** — Parquet 직렬화
- **s3fs** — S3 호환 파일시스템
- **MinIO** — 로컬 오브젝트 스토리지
- **dbt-duckdb** — SQL 변환 레이어 (star schema, SCD snapshot)
- **Docker Compose** — 로컬 환경 구성
