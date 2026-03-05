{{ config(materialized = 'table') }}

SELECT 
    s.STORE_TYPE,
    YEAR(f.STORE_DATE)                  AS SALES_YEAR,
    MONTH(f.STORE_DATE)                 AS SALES_MONTH,
    TO_VARCHAR(f.STORE_DATE, 'YYYY-MM') AS YEAR_MONTH,  -- Format to year-month (e.g: 2010-02)
    AVG(f.STORE_WEEKLY_SALES)           AS AVG_WEEKLY_SALES,
    SUM(f.STORE_WEEKLY_SALES)           AS TOTAL_SALES,
    COUNT(DISTINCT f.STORE_ID)          AS NUM_STORES,
    CURRENT_TIMESTAMP()                 AS INSERT_DATE,
    CURRENT_TIMESTAMP()                 AS UPDATE_DATE

FROM {{ ref('walmart_fact_table')}} f
JOIN {{ref('walmart_store_dim')}} s ON s.STORE_ID = f.STORE_ID

WHERE f.VRSN_END_DATE IS NULL

GROUP BY
    s.STORE_TYPE,
    YEAR(f.STORE_DATE),
    MONTH(f.STORE_DATE),
    TO_VARCHAR(f.STORE_DATE, 'YYYY-MM')

ORDER BY YEAR_MONTH, s.STORE_TYPE 