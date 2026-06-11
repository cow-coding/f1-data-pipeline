# F1 Data Pipeline

OpenF1 API 데이터를 수집하여 Parquet으로 적재하고, dbt로 변환하는 배치 데이터 파이프라인 실습 프로젝트입니다.

## Architecture

```
OpenF1 API
    ↓
Event Generator      # OpenF1 API polling → Collector HTTP POST
    ↓
Collector            # FastAPI + Async Buffer → MinIO Parquet 적재
    ↓
MinIO (Object Storage)   # event_type / date / hour 파티셔닝
    ↓
dbt (DuckDB)         # Staging (incremental) → Mart (table)
    ↓
Analytics
```

## Services

| Service | Description |
|---|---|
| `event-generator` | OpenF1 API를 폴링하여 Collector로 이벤트 전송 |
| `collector` | 이벤트 수신, 전처리 후 MinIO에 Parquet으로 버퍼 플러시 |
| `minio` | S3 호환 로컬 오브젝트 스토리지 |
| `dbt` | staging/mart 레이어 SQL 변환 (DuckDB + dbt-duckdb) |

## Data Sources

[OpenF1 API](https://openf1.org/) 에서 아래 5개 엔드포인트를 수집합니다.

- `car_data` — 속도, RPM, 기어, 스로틀, 브레이크, DRS
- `position` — 드라이버 X/Y/Z 좌표
- `pit` — 피트스탑 정보
- `weather` — 기온, 노면온도, 습도, 풍속, 강수량
- `race_control` — 레이스 컨트롤 메시지, 플래그

## Storage Schema

MinIO에 Hive 스타일 파티셔닝으로 저장됩니다.

```
s3://f1-raw/raw/
└── event_type=car_data/
    └── date=2024-03-02/
        └── hour=14/
            └── part-{timestamp}-0.parquet
```

## Collector Buffer

- 버퍼에 **100건** 이상 쌓이거나 **시간(hour)이 바뀌면** MinIO에 플러시
- 쓰기 실패 시 **3회 backoff 재시도**
- 최종 실패 시 로컬 **Dead Letter Queue** (JSON) 에 저장 후 다음 플러시 때 재처리

## dbt Models

```
staging/
├── stg_car_data          # incremental (emitted_at 기준)
├── stg_position_data     # incremental
├── stg_pit_data          # incremental
├── stg_weather_data      # incremental
└── stg_race_control_data # incremental

mart/
└── mart_driver_performance   # table (avg_speed, max_speed, pit_count)
```

### dbt Tests

모든 staging 모델에 아래 테스트가 적용되어 있습니다.

- `not_null` — `event_id`
- `dbt_utils.recency` — `emitted_at` 기준 2시간 이내 데이터 존재 여부

## Quick Start

### 1. 전체 서비스 실행

```bash
docker-compose up --build
```

MinIO Console: http://localhost:9001 (minioadmin / minioadmin)  
Collector API: http://localhost:8000

### 2. dbt 설정

`~/.dbt/profiles.yml` 에 아래 내용을 추가합니다.

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

```bash
cd transform/f1_dbt
dbt deps       # 패키지 설치
dbt run        # 모델 실행
dbt test       # 데이터 품질 테스트
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
- **dbt-duckdb** — SQL 변환 레이어
- **Docker Compose** — 로컬 환경 구성
