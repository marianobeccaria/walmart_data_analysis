{{ config(
    materialized         = 'incremental',
    unique_key           = ['STORE_ID', 'DEPT_ID'],
    incremental_strategy = 'merge'
) }}

WITH stores AS (
    SELECT STORE_ID, STORE_TYPE, STORE_SIZE
    FROM {{ source('bronze', 'STORES_RAW') }}
),

depts AS (
    SELECT DISTINCT
        CAST(STORE_ID AS INT) AS STORE_ID,
        CAST(DEPT_ID  AS INT) AS DEPT_ID
    FROM {{ source('bronze', 'DEPARTMENT_RAW') }}
),

final AS (
    SELECT
        d.STORE_ID,
        d.DEPT_ID,
        s.STORE_TYPE,
        CAST(s.STORE_SIZE AS INT) AS STORE_SIZE,
        CURRENT_TIMESTAMP()       AS INSERT_DATE,
        CURRENT_TIMESTAMP()       AS UPDATE_DATE
    FROM depts d
    LEFT JOIN stores s ON CAST(s.STORE_ID AS INT) = d.STORE_ID

    -- Deduplicate just in case
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY d.STORE_ID, d.DEPT_ID 
        ORDER BY d.STORE_ID
    ) = 1
)

SELECT * FROM final