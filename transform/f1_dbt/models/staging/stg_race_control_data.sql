{{ config(materialized='incremental') }}
SELECT
    event_id,
    event_type,
    json_extract(payload, '$.message')::VARCHAR AS message,
    json_extract(payload, '$.flag')::VARCHAR AS flag,
    json_extract(payload, '$.lap_number')::INTEGER AS lap_number,
    json_extract(payload, '$.session_key')::INTEGER AS session_key,
    "date",
    "hour",
    emitted_at
FROM read_parquet('s3://f1-raw/raw/event_type=race_control/**/*.parquet')
{% if is_incremental() %}
WHERE emitted_at > (SELECT MAX(emitted_at) FROM {{ this }})
{% endif %}