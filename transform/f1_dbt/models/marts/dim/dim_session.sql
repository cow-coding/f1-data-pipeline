{{ config(materialized='table') }}
SELECT DISTINCT
    session_key,
    session_name,
    circuit,
    country
FROM {{ ref('stg_car_data') }}