-- write a unpacking query here based on test_collector.py 's position data schema
SELECT
    event_id,
    event_type,
    json_extract(payload, '$.driver_number')::INTEGER AS driver_number,
    json_extract(payload, '$.x')::INTEGER AS x,
    json_extract(payload, '$.y')::INTEGER AS y,
    json_extract(payload, '$.z')::INTEGER AS z,
    json_extract(payload, '$.session_key')::INTEGER AS session_key,
    "date",
    "hour",
    emitted_at
FROM read_parquet('s3://f1-raw/raw/event_type=position/**/*.parquet')