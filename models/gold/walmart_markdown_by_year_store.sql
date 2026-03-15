-- models/gold/walmart_markdown_by_year_store.sql
{{ config(materialized = 'table') }}

WITH store_type AS (
    -- Get one store type per store using MAX to deduplicate
    SELECT
        STORE_ID,
        MAX(STORE_TYPE) AS STORE_TYPE
    FROM {{ ref('walmart_store_dim') }}
    GROUP BY STORE_ID
),

base AS (
    SELECT
        f.STORE_ID,
        s.STORE_TYPE,
        YEAR(f.STORE_DATE)                      AS SALES_YEAR,
        SUM(f.STORE_WEEKLY_SALES)               AS TOTAL_SALES,
        AVG(f.MARKDOWN1)                        AS AVG_MARKDOWN1,
        AVG(f.MARKDOWN2)                        AS AVG_MARKDOWN2,
        AVG(f.MARKDOWN3)                        AS AVG_MARKDOWN3,
        AVG(f.MARKDOWN4)                        AS AVG_MARKDOWN4,
        AVG(f.MARKDOWN5)                        AS AVG_MARKDOWN5,
        SUM(COALESCE(f.MARKDOWN1, 0))           AS TOTAL_MARKDOWN1,
        SUM(COALESCE(f.MARKDOWN2, 0))           AS TOTAL_MARKDOWN2,
        SUM(COALESCE(f.MARKDOWN3, 0))           AS TOTAL_MARKDOWN3,
        SUM(COALESCE(f.MARKDOWN4, 0))           AS TOTAL_MARKDOWN4,
        SUM(COALESCE(f.MARKDOWN5, 0))           AS TOTAL_MARKDOWN5,
        SUM(
            COALESCE(f.MARKDOWN1, 0) +
            COALESCE(f.MARKDOWN2, 0) +
            COALESCE(f.MARKDOWN3, 0) +
            COALESCE(f.MARKDOWN4, 0) +
            COALESCE(f.MARKDOWN5, 0)
        )                                       AS TOTAL_ALL_MARKDOWNS,
        CURRENT_TIMESTAMP()                     AS INSERT_DATE,
        CURRENT_TIMESTAMP()                     AS UPDATE_DATE
    FROM {{ ref('walmart_fact_table') }} f
    LEFT JOIN store_type s ON f.STORE_ID = s.STORE_ID
    WHERE f.VRSN_END_DATE IS NULL
    GROUP BY
        f.STORE_ID,
        s.STORE_TYPE,
        YEAR(f.STORE_DATE)
)

SELECT * FROM base
ORDER BY SALES_YEAR, STORE_ID