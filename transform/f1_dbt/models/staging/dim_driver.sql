{{ config(materialized='table') }}

SELECT DISTINCT
    json_extract(payload, '$.driver_number')::INTEGER AS driver_number,
    json_extract(payload, '$.driver_name')::VARCHAR   AS driver_name,
    json_extract(payload, '$.team_name')::VARCHAR     AS team_name,
    json_extract(payload, '$.name_acronym')::VARCHAR  AS name_acronym
FROM read_parquet('s3://f1-raw/raw/event_type=car_data/**/*.parquet')
WHERE json_extract(payload, '$.driver_name') IS NOT NULL
