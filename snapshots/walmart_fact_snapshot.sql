{% snapshot walmart_fact_snapshot %}

{{
    config(
        target_database = var('target_db'),
        target_schema   = 'SILVER',
        unique_key      = ['STORE_ID', 'DEPT_ID', 'STORE_DATE'],
        strategy        = 'check',
        check_cols      = [
                            'STORE_WEEKLY_SALES',
                            'FUEL_PRICE',
                            'TEMPERATURE',
                            'CPI',
                            'UNEMPLOYMENT',
                            'MARKDOWN1',
                            'MARKDOWN2',
                            'MARKDOWN3',
                            'MARKDOWN4',
                            'MARKDOWN5'
                          ]
    )
}}

WITH dept_raw AS (
    SELECT
        CAST(STORE_ID    AS INT)                AS STORE_ID,
        CAST(DEPT_ID     AS INT)                AS DEPT_ID,
        TO_DATE(STORE_DATE, 'YYYY-MM-DD')       AS STORE_DATE,
        TRY_CAST(WEEKLY_SALES AS DECIMAL(18,2)) AS STORE_WEEKLY_SALES
    FROM {{ source('bronze', 'DEPARTMENT_RAW') }}
    WHERE STORE_DATE IS NOT NULL
),

fact_raw AS (
    SELECT
        CAST(STORE_ID AS INT)                       AS STORE_ID,
        TO_DATE(STORE_DATE, 'YYYY-MM-DD')           AS STORE_DATE,
        TRY_CAST(TEMPERATURE  AS DECIMAL(10,4))     AS TEMPERATURE,
        TRY_CAST(FUEL_PRICE   AS DECIMAL(10,4))     AS FUEL_PRICE,
        TRY_CAST(CPI          AS DECIMAL(18,4))     AS CPI,
        TRY_CAST(UNEMPLOYMENT AS DECIMAL(10,4))     AS UNEMPLOYMENT,
        TRY_CAST(MARKDOWN1    AS DECIMAL(18,2))     AS MARKDOWN1,
        TRY_CAST(MARKDOWN2    AS DECIMAL(18,2))     AS MARKDOWN2,
        TRY_CAST(MARKDOWN3    AS DECIMAL(18,2))     AS MARKDOWN3,
        TRY_CAST(MARKDOWN4    AS DECIMAL(18,2))     AS MARKDOWN4,
        TRY_CAST(MARKDOWN5    AS DECIMAL(18,2))     AS MARKDOWN5
    FROM {{ source('bronze', 'FACT_RAW') }}
    WHERE STORE_DATE IS NOT NULL
),

date_dim AS (
    SELECT
        DATE_ID,
        STORE_DATE
    FROM {{ ref('walmart_date_dim') }}
),

store_dim AS (
    SELECT
        STORE_ID,
        DEPT_ID,
        STORE_TYPE,
        STORE_SIZE
    FROM {{ ref('walmart_store_dim') }}
),

joined AS (
    SELECT
        -- Keys
        d.STORE_ID,
        d.DEPT_ID,
        dd.DATE_ID,
        d.STORE_DATE,

        -- Store attributes (from store dim)
        s.STORE_TYPE,
        s.STORE_SIZE,

        -- Measures
        d.STORE_WEEKLY_SALES,
        f.FUEL_PRICE,
        f.TEMPERATURE,
        f.CPI,
        f.UNEMPLOYMENT,
        f.MARKDOWN1,
        f.MARKDOWN2,
        f.MARKDOWN3,
        f.MARKDOWN4,
        f.MARKDOWN5,

        -- Audit columns
        CURRENT_TIMESTAMP() AS INSERT_DATE,
        CURRENT_TIMESTAMP() AS UPDATE_DATE

    FROM dept_raw d
    LEFT JOIN fact_raw  f  ON  d.STORE_ID   = f.STORE_ID
                           AND d.STORE_DATE  = f.STORE_DATE
    LEFT JOIN date_dim  dd ON  d.STORE_DATE  = dd.STORE_DATE
    LEFT JOIN store_dim s  ON  d.STORE_ID    = s.STORE_ID
                           AND d.DEPT_ID     = s.DEPT_ID
)

SELECT * FROM joined

{% endsnapshot %}