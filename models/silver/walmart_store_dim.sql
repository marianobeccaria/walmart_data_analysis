
{{ config(
    materialized = 'incremental',
    unique_key   = 'STORE_ID',
    incremental_strategy = 'merge'
) }}

WITH stores AS (
    SELECT STORE_ID, STORE_TYPE, STORE_SIZE
    FROM {{ source('bronze', 'STORES_RAW') }}
),
depts AS (
    SELECT STORE_ID, DEPT_ID
    FROM {{ source('bronze', 'DEPARTMENT_RAW') }}
),
final AS (
    SELECT 
        CAST(d.STORE_ID AS INT) AS STORE_ID,
        CAST(d.DEPT_ID AS INT) AS DEPT_ID, 
        s.STORE_TYPE, 
        CAST(s.STORE_SIZE AS INT) AS STORE_SIZE,
        CURRENT_TIMESTAMP() AS INSERT_DATE,
        CURRENT_TIMESTAMP() AS UPDATE_DATE
    FROM depts d 
    LEFT JOIN stores s ON s.STORE_ID = d.STORE_ID
)

SELECT * FROM final

-- incremantal condition to get new records that are not already
{% if is_incremental() %}
    -- this filter will only be applied on an incremental run
    where (STORE_ID, DEPT_ID) NOT IN ( SELECT STORE_ID, DEPT_ID from {{ this }}) 
{% endif %}