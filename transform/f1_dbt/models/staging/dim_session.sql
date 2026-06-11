{{ config(materialized='table') }}

SELECT DISTINCT
    json_extract(payload, '$.session_key')::INTEGER AS session_key,
    json_extract(payload, '$.session_name')::VARCHAR AS session_name,
    json_extract(payload, '$.circuit')::VARCHAR      AS circuit,
    json_extract(payload, '$.country')::VARCHAR      AS country
FROM read_parquet('s3://f1-raw/raw/event_type=car_data/**/*.parquet')
WHERE json_extract(payload, '$.session_name') IS NOT NULL
