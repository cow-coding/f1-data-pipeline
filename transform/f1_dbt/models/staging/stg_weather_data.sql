SELECT
    event_id,
    event_type,
    json_extract(payload, '$.air_temperature')::INTEGER AS air_temperature,
    json_extract(payload, '$.track_temperature')::INTEGER AS track_temperature,
    json_extract(payload, '$.humidity')::INTEGER AS humidity,
    json_extract(payload, '$.wind_speed')::INTEGER AS wind_speed,
    json_extract(payload, '$.rainfall')::INTEGER AS rainfall,
    json_extract(payload, '$.session_key')::INTEGER AS session_key,
    "date",
    "hour",
    emitted_at
FROM read_parquet('s3://f1-raw/raw/event_type=weather/**/*.parquet')