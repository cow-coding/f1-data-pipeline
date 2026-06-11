{{ config(materialized='table') }}
SELECT
    event_id,
    event_type,
    driver_number,
    speed,
    rpm,
    gear,
    throttle,
    brake,
    drs,
    session_key,
    "date",
    "hour",
    emitted_at
FROM {{ ref('stg_car_data') }}