{{ config(materialized='table') }}
SELECT DISTINCT
    driver_number,
    driver_name,
    team_name,
    name_acronym
FROM {{ ref('driver_snapshot') }}
WHERE dbt_valid_to IS NULL