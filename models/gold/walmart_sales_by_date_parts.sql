{{ config(materialized = 'table') }}

-- Weekly sales by year, month
SELECT
    f.STORE_DATE,
    YEAR(f.STORE_DATE)                  AS SALES_YEAR,
    MONTH(f.STORE_DATE)                 AS SALES_MONTH,
    MONTHNAME(f.STORE_DATE)             AS MONTH_NAME,
    WEEKOFYEAR(f.STORE_DATE)            AS WEEK_OF_YEAR,
    TO_VARCHAR(f.STORE_DATE, 'YYYY-MM') AS YEAR_MONTH,
    d.ISHOLIDAY,
    SUM(f.STORE_WEEKLY_SALES)           AS TOTAL_SALES,
    AVG(f.STORE_WEEKLY_SALES)           AS AVG_WEEKLY_SALES,
    COUNT(f.STORE_ID)                   AS NUM_StORES,
    CURRENT_TIMESTAMP()                 AS INSERT_DATE,
    CURRENT_TIMESTAMP()                 AS UPDATE_DATE

FROM {{ ref('walmart_fact_table') }} f 
LEFT JOIN {{ ref('walmart_date_dim') }} d  ON d.STORE_DATE = f.STORE_DATE

WHERE f.VRSN_END_DATE IS NULL

GROUP BY 
    f.STORE_DATE,
    YEAR(f.STORE_DATE),
    MONTH(f.STORE_DATE),
    MONTHNAME(f.STORE_DATE),
    WEEKOFYEAR(f.STORE_DATE),
    TO_VARCHAR(f.STORE_DATE, 'YYYY-MM'),
    d.ISHOLIDAY

ORDER BY f.STORE_DATE