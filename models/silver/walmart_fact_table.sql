{{ config(
    materialized         = 'incremental',
    unique_key           = 'SNAPSHOT_KEY',
    incremental_strategy = 'merge'
) }}

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
        CAST(STORE_ID AS INT)                   AS STORE_ID,
        TO_DATE(STORE_DATE, 'YYYY-MM-DD')       AS STORE_DATE,
        TRY_CAST(TEMPERATURE  AS DECIMAL(10,4)) AS TEMPERATURE,
        TRY_CAST(FUEL_PRICE   AS DECIMAL(10,4)) AS FUEL_PRICE,
        TRY_CAST(CPI          AS DECIMAL(18,4)) AS CPI,
        TRY_CAST(UNEMPLOYMENT AS DECIMAL(10,4)) AS UNEMPLOYMENT,
        TRY_CAST(MARKDOWN1    AS DECIMAL(18,2)) AS MARKDOWN1,
        TRY_CAST(MARKDOWN2    AS DECIMAL(18,2)) AS MARKDOWN2,
        TRY_CAST(MARKDOWN3    AS DECIMAL(18,2)) AS MARKDOWN3,
        TRY_CAST(MARKDOWN4    AS DECIMAL(18,2)) AS MARKDOWN4,
        TRY_CAST(MARKDOWN5    AS DECIMAL(18,2)) AS MARKDOWN5
    FROM {{ source('bronze', 'FACT_RAW') }}
    WHERE STORE_DATE IS NOT NULL
),

date_dim AS (
    SELECT DATE_ID, STORE_DATE
    FROM {{ ref('walmart_date_dim') }}
),

store_dim AS (
    SELECT STORE_ID, DEPT_ID, STORE_TYPE, STORE_SIZE
    FROM {{ ref('walmart_store_dim') }}
),

joined AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key([
            'd.STORE_ID',
            'd.DEPT_ID',
            'd.STORE_DATE'
        ]) }}                                   AS SNAPSHOT_KEY,
        d.STORE_ID,
        d.DEPT_ID,
        dd.DATE_ID,
        d.STORE_DATE,
        s.STORE_TYPE,
        s.STORE_SIZE,
        d.STORE_WEEKLY_SALES,
        f.FUEL_PRICE,
        f.TEMPERATURE,
        f.CPI,
        f.UNEMPLOYMENT,
        f.MARKDOWN1,
        f.MARKDOWN2,
        f.MARKDOWN3,
        f.MARKDOWN4,
        f.MARKDOWN5
    FROM dept_raw d
    LEFT JOIN fact_raw  f  ON  d.STORE_ID  = f.STORE_ID
                           AND d.STORE_DATE = f.STORE_DATE
    LEFT JOIN date_dim  dd ON  d.STORE_DATE = dd.STORE_DATE
    LEFT JOIN store_dim s  ON  d.STORE_ID   = s.STORE_ID
                           AND d.DEPT_ID    = s.DEPT_ID
),

-- SCD2 logic: detect changed rows by comparing against existing table
scd2 AS (
    SELECT
        j.SNAPSHOT_KEY,
        j.STORE_ID,
        j.DEPT_ID,
        j.DATE_ID,
        j.STORE_DATE,
        j.STORE_TYPE,
        j.STORE_SIZE,
        j.STORE_WEEKLY_SALES,
        j.FUEL_PRICE,
        j.TEMPERATURE,
        j.CPI,
        j.UNEMPLOYMENT,
        j.MARKDOWN1,
        j.MARKDOWN2,
        j.MARKDOWN3,
        j.MARKDOWN4,
        j.MARKDOWN5,
        CURRENT_TIMESTAMP()     AS VRSN_START_DATE,
        NULL                    AS VRSN_END_DATE,
        CURRENT_TIMESTAMP()     AS INSERT_DATE,
        CURRENT_TIMESTAMP()     AS UPDATE_DATE

    FROM joined j

    {% if is_incremental() %}
    -- Only process rows that are new or have changed values
    WHERE j.SNAPSHOT_KEY NOT IN (
        SELECT SNAPSHOT_KEY 
        FROM {{ this }}
        WHERE VRSN_END_DATE IS NULL
    )
    OR j.SNAPSHOT_KEY IN (
        SELECT t.SNAPSHOT_KEY
        FROM {{ this }} t
        JOIN joined src ON t.SNAPSHOT_KEY = src.SNAPSHOT_KEY
        WHERE t.VRSN_END_DATE IS NULL
        AND (
            t.STORE_WEEKLY_SALES != src.STORE_WEEKLY_SALES OR
            t.FUEL_PRICE         != src.FUEL_PRICE         OR
            t.TEMPERATURE        != src.TEMPERATURE        OR
            t.CPI                != src.CPI                OR
            t.UNEMPLOYMENT       != src.UNEMPLOYMENT
        )
    )
    {% endif %}
)

SELECT * FROM scd2