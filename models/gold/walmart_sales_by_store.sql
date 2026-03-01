{{  config(
        materialized='table'
)}}

SELECT 
    f.STORE_ID,
    s.STORE_TYPE,
    s.STORE_SIZE,
    COUNT(DISTINCT f.STORE_DATE)    AS WEEKS_OF_DATA,
    SUM(f.STORE_WEEKLY_SALES)       AS TOTAL_SALES,
    AVG(f.STORE_WEEKLY_SALES)       AS AVG_WEEKLY_SALES,
    MAX(f.STORE_WEEKLY_SALES)       AS MAX_WEEKLY_SALES,
    MIN(f.STORE_WEEKLY_SALES)       AS MIN_WEEKLY_SALES,
    CURRENT_TIMESTAMP()             AS INSERT_DATE,
    CURRENT_TIMESTAMP()             AS UPDATE_DATE

FROM {{ ref('walmart_fact_snapshot') }} f 
JOIN {{ ref('walmart_store_dim') }} s ON s.STORE_ID = f.STORE_ID

WHERE f.DBT_VALID_TO IS NULL  -- Only current active records

GROUP BY f.STORE_ID, s.STORE_TYPE, s.STORE_SIZE
ORDER BY TOTAL_SALES DESC