{% macro macros_copy_csv() %}

    {% set load_stores %}
        COPY INTO {{ var('target_db') }}.{{ var('target_schema') }}.STORES_RAW 
            (STORE_ID, STORE_TYPE, STORE_SIZE)
        FROM @{{ var('stage_name') }}/stores.csv
        FILE_FORMAT = (FORMAT_NAME = '{{ var("file_format_csv") }}')
        ON_ERROR = 'CONTINUE';
    {% endset %}

    {% set load_department %}
        COPY INTO {{ var('target_db') }}.{{ var('target_schema') }}.DEPARTMENT_RAW 
            (STORE_ID, DEPT_ID, STORE_DATE, WEEKLY_SALES, ISHOLIDAY)
        FROM @{{ var('stage_name') }}/department.csv
        FILE_FORMAT = (FORMAT_NAME = '{{ var("file_format_csv") }}')
        ON_ERROR = 'CONTINUE';
    {% endset %}

    {% set load_fact %}
        COPY INTO {{ var('target_db') }}.{{ var('target_schema') }}.FACT_RAW 
            (STORE_ID, STORE_DATE, TEMPERATURE, FUEL_PRICE, MARKDOWN1, MARKDOWN2, 
             MARKDOWN3, MARKDOWN4, MARKDOWN5, CPI, UNEMPLOYMENT, ISHOLIDAY)
        FROM @{{ var('stage_name') }}/fact.csv
        FILE_FORMAT = (FORMAT_NAME = '{{ var("file_format_csv") }}')
        ON_ERROR = 'CONTINUE';
    {% endset %}

    {{ run_query(load_stores) }}
    {{ log("✅ Loaded STORES_RAW", info=true) }}

    {{ run_query(load_department) }}
    {{ log("✅ Loaded DEPARTMENT_RAW", info=true) }}

    {{ run_query(load_fact) }}
    {{ log("✅ Loaded FACT_RAW", info=true) }}

{% endmacro %}