-- car_data는 먼저 집계하고
WITH car_stats AS (
    SELECT driver_number,
           AVG(speed) AS avg_speed,
           MAX(speed) AS max_speed
    FROM {{ ref('stg_car_data') }}
    GROUP BY driver_number
),
-- pit_data도 먼저 집계하고
pit_stats AS (
    SELECT driver_number,
           COUNT(*) AS pit_count
    FROM {{ ref('stg_pit_data') }}
    GROUP BY driver_number
)
-- 집계된 결과끼리 조인
SELECT c.driver_number, avg_speed, max_speed, pit_count
FROM car_stats c
LEFT JOIN pit_stats p ON c.driver_number = p.driver_number