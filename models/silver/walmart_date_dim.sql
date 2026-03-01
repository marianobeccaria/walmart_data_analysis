-- models/silver/walmart_date_dim.sql
{{ config(
    materialized = 'incremental',
    unique_key   = 'DATE_ID',
    incremental_strategy = 'merge'
) }}

WITH source AS (
    SELECT DISTINCT
        TO_DATE(STORE_DATE, 'YYYY-MM-DD')  AS STORE_DATE,
        ISHOLIDAY
    FROM {{ source('bronze', 'DEPARTMENT_RAW') }}
    WHERE STORE_DATE IS NOT NULL
)
SELECT
    ROW_NUMBER() OVER (ORDER BY STORE_DATE)  AS DATE_ID,
    STORE_DATE,
    ISHOLIDAY,
    CURRENT_TIMESTAMP()                      AS INSERT_DATE,
    CURRENT_TIMESTAMP()                      AS UPDATE_DATE
FROM source

-- Incremental condition only for recorsds with a new STORE_DATE
{% if is_incremental() %}
    -- this filter will only be applied on an incremental run
    where  STORE_DATE NOT IN (select STORE_DATE from {{ this }}) 
{% endif %}