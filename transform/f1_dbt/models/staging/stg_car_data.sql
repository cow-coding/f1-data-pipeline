{{  config(materialized='incremental') }}
SELECT
    event_id,
    event_type,
    json_extract(payload, '$.driver_number')::INTEGER AS driver_number,
    json_extract(payload, '$.speed')::INTEGER AS speed,
    json_extract(payload, '$.rpm')::INTEGER AS rpm,
    json_extract(payload, '$.gear')::INTEGER AS gear,
    json_extract(payload, '$.throttle')::INTEGER AS throttle,
    json_extract(payload, '$.brake')::INTEGER AS brake,
    json_extract(payload, '$.drs')::INTEGER AS drs,
    json_extract(payload, '$.session_key')::INTEGER AS session_key,
    "date",
    "hour",
    emitted_at
FROM read_parquet('s3://f1-raw/raw/event_type=car_data/**/*.parquet')
{% if is_incremental() %}
WHERE emitted_at > (SELECT MAX(emitted_at) FROM {{ this }})
{% endif %}