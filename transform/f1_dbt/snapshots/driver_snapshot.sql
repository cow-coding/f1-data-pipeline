{% snapshot driver_snapshot %}
{{
    config(
        target_schema='snapshots',
        unique_key='driver_number',
        strategy='check',
        check_cols=['team_name', 'driver_name']
    )
}}
SELECT DISTINCT
    driver_number,
    driver_name,
    team_name,
    name_acronym
FROM {{ ref('stg_car_data') }}
{% endsnapshot %}