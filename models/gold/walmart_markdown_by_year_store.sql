{{ config(materialized = 'table') }}

SELECT 
    f.STORE_ID,
    s.STORE_TYPE,
    YEAR(f.STORE_DATE)          AS SALES_YEAR,
    SUM(f.STORE_WEEKLY_SALES)   AS TOTAL_SALES,
    -- Averages for each type of markdown
    AVG(f.MARKDOWN1)            AS AVG_MARKDOWN1,
    AVG(f.MARKDOWN2)            AS AVG_MARKDOWN2,
    AVG(f.MARKDOWN3)            AS AVG_MARKDOWN3,
    AVG(f.MARKDOWN4)            AS AVG_MARKDOWN4,
    AVG(f.MARKDOWN5)            AS AVG_MARKDOWN5,
    -- totals for each type of markdown
    SUM(f.MARKDOWN1)            AS TOTAL_MARKDOWN1,
    SUM(f.MARKDOWN2)            AS TOTAL_MARKDOWN2,
    SUM(f.MARKDOWN3)            AS TOTAL_MARKDOWN3,
    SUM(f.MARKDOWN4)            AS TOTAL_MARKDOWN4,
    SUM(f.MARKDOWN5)            AS TOTAL_MARKDOWN5,
    -- total for all 5 comined markdowsn
    SUM(COALESCE(f.MARKDOWN1, 0) +
        COALESCE(f.MARKDOWN2, 0) +
        COALESCE(f.MARKDOWN3, 0) +
        COALESCE(f.MARKDOWN4, 0) +
        COALESCE(f.MARKDOWN5, 0) 
    )                           AS TOTAL_ALL_MARKDOWNS,

    CURRENT_TIMESTAMP()         AS INSERT_DATE,
    CURRENT_TIMESTAMP()         AS UPDATE_DATE

FROM {{ ref('walmart_fact_table') }} f
LEFT JOIN {{ ref('walmart_store_dim')}} s 

WHERE f.VRSN_END_DATE IS NULL

GROUP BY f.STORE_ID, s.STORE_TYPE, YEAR(STORE_DATE)

ORDER BY SALES_YEAR, TOTAL_SALES