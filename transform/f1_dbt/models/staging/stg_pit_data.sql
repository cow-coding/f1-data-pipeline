SELECT
    event_id,
    event_type,
    json_extract(payload, '$.driver_number')::INTEGER AS driver_number,
    json_extract(payload, '$.lap_number')::INTEGER AS lap_number,
    json_extract(payload, '$.pit_duration')::FLOAT AS pit_duration,
    json_extract(payload, '$.session_key')::INTEGER AS session_key,
    "date",
    "hour",
    emitted_at
FROM read_parquet('s3://f1-raw/raw/event_type=pit/**/*.parquet')