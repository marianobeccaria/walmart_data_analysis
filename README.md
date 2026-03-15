# Walmart BI Data Analysis Project

## Table of Contents
- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Data Pipeline](#data-pipeline)
- [Bronze Layer](#bronze-layer)
- [Silver Layer](#silver-layer)
- [Gold Layer](#gold-layer)
- [Reports & Charts](#reports--charts)
- [How to Run](#how-to-run)
- [SCD2 Implementation History](#scd2-implementation-history)
- [Snapshot Verification Tests](#snapshot-verification-tests)

---

## Project Overview

This project implements an end-to-end Business Intelligence pipeline for analyzing Walmart store sales data. Raw CSV files are ingested from AWS S3, transformed through a Medallion Architecture (Bronze → Silver → Gold) using Snowflake and dbt, and visualized through Python-generated charts.

The analysis covers 45 Walmart stores across 143 weeks of sales data (2010–2012), examining weekly sales performance across departments, store types, economic factors, and promotional markdowns.

---

## Technology Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Cloud Storage | AWS S3 | Raw CSV file storage |
| Data Warehouse | Snowflake | Database, schemas, staging |
| Transformation | dbt (Data Build Tool) | Data modeling, testing, documentation |
| Orchestration | dbt macros | Bronze loading automation |
| Visualization | Python (matplotlib) | Report charts |
| Environment | Conda / venv | Python dependency management |
| Version Control | Git | Source code management |

---

## Architecture

```
AWS S3 (raw CSV files)
        │
        ▼
┌─────────────────┐
│  BRONZE Schema  │  Raw landing tables — VARCHAR everything
│  Snowflake      │  Loaded via COPY INTO using dbt macros
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SILVER Schema  │  Cleaned, typed, versioned dimension
│  dbt models     │  and fact tables (SCD1 / SCD2 snapshot)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GOLD Schema    │  Aggregated, report-ready tables
│  dbt models     │  optimized for BI and Python charts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Python Charts  │  matplotlib visualizations
│  reports/       │  saved as PNG files
└─────────────────┘
```

---

## Project Structure

```
walmart_data_analysis/
│
├── dbt_project.yml              # dbt project configuration
├── packages.yml                 # dbt packages (dbt_utils 1.3.3)
├── profiles.yml                 # Snowflake connection profile
│
├── macros/
│   ├── macros_copy_csv.sql      # Reusable COPY INTO macro
│   ├── load_all_bronze.sql      # Orchestrates all 3 bronze loads
│   ├── generate_schema_name.sql # Schema naming override
│   └── query_tags.sql           # Snowflake query tag utility
│
├── models/
│   ├── sources.yml              # Bronze table source definitions
│   │
│   ├── silver/
│   │   ├── silver.yml           # Silver model definitions & tests
│   │   ├── walmart_date_dim.sql
│   │   └── walmart_store_dim.sql
│   │
│   └── gold/
│       ├── gold.yml
│       ├── walmart_sales_by_store.sql
│       ├── walmart_sales_by_dept.sql
│       ├── walmart_sales_by_date_parts.sql
│       ├── walmart_sales_by_storetype_month.sql
│       ├── walmart_markdown_by_year_store.sql
│       ├── walmart_holiday_impact.sql
│       └── walmart_economic_factors.sql
│
├── snapshots/
│   ├── schema.yml                 # Snapshot definitions & tests
│   └── walmart_fact_snapshot.sql  # SCD2 fact table via dbt snapshot
│
└── reports/
    ├── connection.py            # Reusable Snowflake connection module
    ├── .env                     # Snowflake credentials (never commit)
    ├── walmart_sales_by_store.py
    ├── walmart_sales_by_dept.py
    ├── walmart_holiday_impact.py
    ├── walmart_sales_by_date_parts.py
    ├── walmart_sales_by_storetype_month.py
    ├── walmart_markdown_by_year_store.py
    ├── walmart_economic_factors.py
    └── charts/                  # Generated PNG chart files
```

---

## Setup & Installation

### Prerequisites
- Snowflake account (free trial works)
- dbt Cloud account or VSCode with dbt-fusion extension
- AWS S3 bucket with raw CSV files
- Python 3.11+ with conda or venv

### Python Environment

```bash
# Create and activate conda environment
conda create -n walmart_env python=3.11
conda activate walmart_env

# Install required packages
pip install snowflake-connector-python pandas matplotlib python-dotenv
```

### Environment Variables

Create a `.env` file in the `reports/` folder:

```bash
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=WALMART_DB
SNOWFLAKE_SCHEMA=GOLD
SNOWFLAKE_ROLE=ACCOUNTADMIN
```

> **Never commit the `.env` file to git.** It is listed in `.gitignore`.

### Snowflake Setup

Run the following in Snowflake to create the initial infrastructure:

```sql
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE DATABASE WALMART_DB;
CREATE OR REPLACE SCHEMA WALMART_DB.BRONZE;
CREATE OR REPLACE SCHEMA WALMART_DB.SILVER;
CREATE OR REPLACE SCHEMA WALMART_DB.GOLD;

-- Create S3 storage integration
CREATE OR REPLACE STORAGE INTEGRATION STORINT_AWS
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'your_role_arn'
  STORAGE_ALLOWED_LOCATIONS = ('s3://your-bucket/raw_data/');

-- Create stage and file format
CREATE OR REPLACE STAGE WALMART_DB.BRONZE.S3_STAGE
  URL = 's3://your-bucket/raw_data/'
  STORAGE_INTEGRATION = STORINT_AWS;

CREATE OR REPLACE FILE FORMAT WALMART_DB.BRONZE.CSV_FORMAT_01
  TYPE = CSV
  FIELD_DELIMITER = ','
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER = 1
  NULL_IF = ('NULL', 'null', 'NA')
  EMPTY_FIELD_AS_NULL = true;
```

---

## Data Pipeline

### Source Data

Three CSV files are uploaded to S3:

| File | Description | Key Columns |
|------|-------------|-------------|
| `stores.csv` | Store metadata | Store, Type, Size |
| `department.csv` | Weekly sales per dept | Store, Dept, Date, Weekly_Sales, IsHoliday |
| `fact.csv` | Economic factors | Store, Date, Temperature, Fuel_Price, MarkDowns, CPI, Unemployment |

---

## Bronze Layer

**Schema:** `WALMART_DB.BRONZE`

The Bronze layer is a raw landing zone. All columns are stored as `VARCHAR` to prevent load failures from bad data (e.g. `NA` values in markdown columns). Two audit columns (`INSERT_DATE`, `UPDATE_DATE`) are added automatically.

### Tables

| Table | Source File | Rows |
|-------|-------------|------|
| `STORES_RAW` | stores.csv | 45 |
| `DEPARTMENT_RAW` | department.csv | 421,570 |
| `FACT_RAW` | fact.csv | 8,190 |

### Loading Bronze Data

Bronze is loaded using a dbt macro rather than a dbt model, since `COPY INTO` is a Snowflake-specific command, not a SQL transformation:

```bash
dbt run-operation load_all_bronze
```

The macro deletes existing data and reloads from S3 using `FORCE = TRUE` to handle file replacement scenarios where new CSVs overwrite existing ones with updated data.

---

## Silver Layer

**Schema:** `WALMART_DB.SILVER`

The Silver layer applies data quality rules, casts all columns to proper types, and implements Slowly Changing Dimension (SCD) logic.

### Models

#### `walmart_date_dim` — SCD Type 1
Date dimension containing one row per unique week in the dataset.

| Column | Type | Description |
|--------|------|-------------|
| DATE_ID | INT | Surrogate primary key |
| STORE_DATE | DATE | Friday of the sales week |
| ISHOLIDAY | VARCHAR | Whether the week contains a US holiday |
| INSERT_DATE | TIMESTAMP | Record creation timestamp |
| UPDATE_DATE | TIMESTAMP | Record last updated timestamp |

**SCD1** means if a date record changes, the existing row is overwritten. No history is kept.

---

#### `walmart_store_dim` — SCD Type 1
Store dimension containing one row per store/department combination.

| Column | Type | Description |
|--------|------|-------------|
| STORE_ID | INT | Store identifier (PK) |
| DEPT_ID | INT | Department identifier (PK) |
| STORE_TYPE | VARCHAR | Store type: A (large), B (medium), C (small) |
| STORE_SIZE | INT | Store floor area in square feet |
| INSERT_DATE | TIMESTAMP | Record creation timestamp |
| UPDATE_DATE | TIMESTAMP | Record last updated timestamp |

Uses `QUALIFY ROW_NUMBER()` to deduplicate and ensure one row per `STORE_ID + DEPT_ID` combination.

---

#### `walmart_fact_snapshot` — SCD Type 2 (dbt snapshot) ✅ Current
Central fact table containing weekly sales and economic measures. Implements SCD2 versioning using a native dbt snapshot so historical records are preserved when data changes.

| Column | Type | Description |
|--------|------|-------------|
| SNAPSHOT_KEY | VARCHAR | Surrogate unique key (hash of STORE_ID + DEPT_ID + DATE) |
| STORE_ID | INT | Foreign key to store_dim |
| DEPT_ID | INT | Foreign key to store_dim |
| DATE_ID | INT | Foreign key to date_dim |
| STORE_DATE | DATE | Week ending date |
| STORE_TYPE | VARCHAR | Store type at time of record |
| STORE_SIZE | INT | Store size at time of record |
| STORE_WEEKLY_SALES | DECIMAL | Weekly sales amount in dollars |
| FUEL_PRICE | DECIMAL | Regional fuel price |
| TEMPERATURE | DECIMAL | Average weekly temperature (°F) |
| CPI | DECIMAL | Consumer Price Index |
| UNEMPLOYMENT | DECIMAL | Regional unemployment rate |
| MARKDOWN1-5 | DECIMAL | Promotional markdown amounts |
| DBT_VALID_FROM | TIMESTAMP | When this version became active |
| DBT_VALID_TO | TIMESTAMP | When this version was superseded (NULL = current) |
| DBT_SCD_ID | VARCHAR | dbt internal snapshot record identifier |
| DBT_UPDATED_AT | TIMESTAMP | When the record was last changed |
| INSERT_DATE | TIMESTAMP | Record creation timestamp |
| UPDATE_DATE | TIMESTAMP | Record last updated timestamp |

**Snapshot strategy:** `check` — dbt compares incoming rows against existing snapshot rows on the specified `check_cols`. If any value has changed, the old record is versioned out and a new one is inserted.

To query only current active records:
```sql
SELECT * FROM WALMART_DB.SILVER.WALMART_FACT_SNAPSHOT
WHERE DBT_VALID_TO IS NULL;
```

To query the full version history for a specific record:
```sql
SELECT STORE_ID, DEPT_ID, STORE_DATE, STORE_WEEKLY_SALES,
       DBT_VALID_FROM, DBT_VALID_TO
FROM WALMART_DB.SILVER.WALMART_FACT_SNAPSHOT
WHERE STORE_ID = 1 AND DEPT_ID = 1 AND STORE_DATE = '2010-02-05'
ORDER BY DBT_VALID_FROM;
```

---

## Gold Layer

**Schema:** `WALMART_DB.GOLD`

The Gold layer contains pre-aggregated, report-ready tables. All Gold models read from Silver (never directly from Bronze) and filter `WHERE DBT_VALID_TO IS NULL` to use only current active snapshot records.

### Models

| Model | Description |
|-------|-------------|
| `walmart_sales_by_store` | Total and avg weekly sales per store, split by holiday |
| `walmart_sales_by_dept` | Total and avg weekly sales per store/department combination |
| `walmart_sales_by_date_parts` | Weekly sales with year, month, week breakdown |
| `walmart_sales_by_storetype_month` | Monthly sales aggregated by store type (A/B/C) |
| `walmart_markdown_by_year_store` | Annual markdown totals by store and markdown type |
| `walmart_holiday_impact` | Holiday vs non-holiday sales comparison |
| `walmart_economic_factors` | Weekly sales alongside CPI, fuel, temperature, unemployment |

---

## Reports & Charts

All charts are generated using Python and saved as PNG files in `reports/charts/`. Each script follows the same pattern: load data once from the Gold layer, then transform and render.

### Connection Pattern

```python
from connection import get_dataframe

df = get_dataframe("SELECT * FROM WALMART_DB.GOLD.YOUR_TABLE")
```

---

### 1. `walmart_sales_by_store.py`
**Requirement:** Weekly sales by store type and store size

Shows total sales per store colored by store type (A/B/C). Type A (large format) stores consistently outperform Type B and C stores.

---

### 2. `walmart_sales_by_dept.py`
**Requirement:** Weekly sales by department

Shows a 4 panel dashboard: total sales by department/store, avg weekly sales, side-by-side comparison, and Min/Avg/Max grouped bar chart. Department 92 is consistently the top performer.

---

### 3. `walmart_holiday_impact.py`
**Requirement:** Weekly sales by store and holiday

Pie chart, KPI cards, and grouped bar chart comparing holiday vs non-holiday sales per store. Holiday weeks show approximately 7% higher average weekly sales.

---

### 4. `walmart_sales_by_date_parts.py`
**Requirement:** Weekly sales by year, month and day

Four-panel time series: full weekly trend with holiday markers, year-over-year comparison, monthly seasonality, and holiday vs non-holiday by month. Clear peaks in November/December.

---

### 5. `walmart_sales_by_storetype_month.py`
**Requirement:** Weekly sales by store type and month

Line chart of monthly trends per store type with a summary table of monthly totals. All types follow similar seasonal patterns with Type A showing highest absolute sales.

---

### 6. `walmart_markdown_by_year_store.py`
**Requirement:** Markdown sales by year and store

Grouped bar chart of markdown amounts by type (MD1-MD5) per year. No markdown data in 2010. Markdown activity increased significantly from 2011 to 2012.

---

### 7. `walmart_economic_factors.py`
**Requirement:** Weekly sales by CPI, temperature, fuel price, and unemployment

Four-panel chart with scatter plots and line charts. Fuel price shows positive correlation with sales; unemployment shows negative correlation.

---

## How to Run

### Full Pipeline (from scratch)

```bash
# Step 1: Load Bronze tables from S3
dbt run-operation load_all_bronze

# Step 2: Build Silver dimension tables
dbt run --full-refresh

# Step 3: Run SCD2 snapshot for fact table
dbt snapshot

# Step 4: Build Gold aggregation tables
dbt run --select gold

# Step 5: Run data quality tests
dbt test

# Step 6: Generate documentation
dbt docs generate
dbt docs serve
```

### Incremental Run (new data loaded to S3)

```bash
dbt run-operation load_all_bronze  # reload Bronze
dbt run                            # update Silver dims
dbt snapshot                       # picks up new/changed rows
dbt run --select gold              # rebuild Gold
```

### Generate Python Charts

```bash
cd reports && conda activate walmart_env

python walmart_sales_by_store.py
python walmart_sales_by_dept.py
python walmart_holiday_impact.py
python walmart_sales_by_date_parts.py
python walmart_sales_by_storetype_month.py
python walmart_markdown_by_year_store.py
python walmart_economic_factors.py
```

---

## dbt Commands Reference

| Command | Purpose |
|---------|---------|
| `dbt run` | Build all models |
| `dbt run --select model_name` | Build a specific model |
| `dbt run --full-refresh` | Rebuild all models from scratch |
| `dbt snapshot` | Run all snapshots |
| `dbt test` | Run all data quality tests |
| `dbt run-operation load_all_bronze` | Load raw CSV data into Bronze |
| `dbt compile` | Generate SQL without executing |
| `dbt docs generate && dbt docs serve` | Build and view documentation |
| `dbt source freshness` | Check Bronze table freshness |
| `dbt system update` | Upgrade dbt-fusion to latest version |

---

## SCD2 Implementation History

The fact table SCD2 implementation went through two iterations. Both are documented here for reference.

---

### Approach 1: dbt Incremental Model (`walmart_fact_table`) — Superseded

The first implementation used a dbt `incremental` model with `merge` strategy and manually managed `VRSN_START_DATE` / `VRSN_END_DATE` versioning columns.

```sql
{{ config(
    materialized         = 'incremental',
    unique_key           = 'SNAPSHOT_KEY',
    incremental_strategy = 'merge'
) }}
```

**Why it was built this way:** Testing of dbt snapshots on dbt-fusion `2.0.0-preview.120` revealed a deduplication bug — the snapshot inserted duplicate rows on every run instead of merging. The incremental model with `QUALIFY ROW_NUMBER()` was used as a reliable workaround.

**Query pattern:**
```sql
SELECT * FROM WALMART_DB.SILVER.WALMART_FACT_TABLE
WHERE VRSN_END_DATE IS NULL;
```

---

### Approach 2: dbt Native Snapshot (`walmart_fact_snapshot`) ✅ Current

After upgrading to dbt-fusion `2.0.0-preview.126`, the snapshot deduplication bug was confirmed fixed. The implementation was migrated to a native dbt snapshot using the `check` strategy.

**Advantages over the incremental approach:**
- dbt manages all versioning logic automatically
- `DBT_VALID_FROM` / `DBT_VALID_TO` handled natively
- Industry standard pattern for SCD2 in dbt
- Cleaner, less custom SQL to maintain

**Why `check` strategy over `timestamp`?** The source CSV files have no reliable `updated_at` column. The `check` strategy compares specific column values on each run to detect changes.

**Query pattern:**
```sql
SELECT * FROM WALMART_DB.SILVER.WALMART_FACT_SNAPSHOT
WHERE DBT_VALID_TO IS NULL;
```

---

## Snapshot Verification Tests

Four tests were performed to verify the snapshot implementation before merging to main.

---

### Test 1: Idempotency ✅

Confirmed that running the snapshot multiple times against unchanged data does not insert duplicate rows.

```bash
dbt snapshot  # run 1 → 421,570 rows
dbt snapshot  # run 2 → 421,570 rows (unchanged)
```

---

### Test 2: SCD2 Versioning Behavior ✅

Confirmed that when a source value changes, the old record is versioned out and a new active record is inserted.

```sql
-- Simulate a correction in Bronze
UPDATE WALMART_DB.BRONZE.DEPARTMENT_RAW
SET WEEKLY_SALES = '99999.99'
WHERE STORE_ID = '1' AND DEPT_ID = '1' AND STORE_DATE = '2010-02-05';
```

After running `dbt snapshot`:

```
STORE_WEEKLY_SALES | DBT_VALID_FROM      | DBT_VALID_TO
24924.50           | 2026-03-15 14:36:01 | 2026-03-15 14:57:43  ← versioned out
99999.99           | 2026-03-15 14:57:43 | NULL                 ← new active record
```

Total rows increased from 421,570 to 421,571 with exactly 1 versioned out row.

---

### Test 3: New Data from S3 ✅

Confirmed that new rows appended to source CSV files and uploaded to S3 flow through the full pipeline correctly.

```bash
# Append new rows to department.csv
cat >> department.csv << 'EOF'
1,1,2013-01-04,25000.00,FALSE
1,2,2013-01-04,18500.00,FALSE
2,1,2013-01-04,31000.00,FALSE
2,2,2013-01-04,22000.00,FALSE
EOF

# Upload and run full pipeline
aws s3 cp department.csv s3://your-bucket/raw_data/department.csv
dbt run-operation load_all_bronze && dbt run && dbt snapshot && dbt run --select gold
```

After the run:
```sql
SELECT MAX(STORE_DATE) FROM WALMART_DB.SILVER.WALMART_FACT_SNAPSHOT
WHERE DBT_VALID_TO IS NULL;
-- Result: 2013-01-04 ✅
```

All 4 new rows appeared correctly as active records.

---

### Test 4: dbt Data Quality Tests ✅

```bash
dbt test
# Result: 8/8 tests passing
```

```
✅ unique_walmart_date_dim_DATE_ID
✅ not_null_walmart_date_dim_DATE_ID
✅ not_null_walmart_date_dim_STORE_DATE
✅ not_null_walmart_store_dim_STORE_ID
✅ not_null_walmart_store_dim_DEPT_ID
✅ unique_combination_of_columns_walmart_store_dim_STORE_ID__DEPT_ID
✅ not_null_walmart_sales_by_store_STORE_ID
✅ unique_combination_of_columns_walmart_sales_by_store_STORE_ID__ISHOLIDAY
```

---

## Key Design Decisions

**Why VARCHAR in Bronze?** The source CSVs contain `NA` values in markdown columns. Using `VARCHAR` ensures `COPY INTO` never fails. All casting happens in Silver using `TRY_CAST()` which returns `NULL` instead of erroring.

**Why SCD2 for the fact table?** Sales data can be retroactively corrected. SCD2 preserves the original record and inserts a new version, allowing historical analysis to reflect what the data looked like at any point in time.

**Why dbt snapshot over incremental?** The native dbt snapshot is the industry standard for SCD2 in dbt. It handles all versioning logic automatically. The incremental model was used initially as a workaround for a bug in dbt-fusion preview versions that was fixed in `2.0.0-preview.126`.

**Why `check` strategy?** The source CSV files have no reliable `updated_at` timestamp. The `check` strategy compares specific column values on each run, working correctly regardless of whether source timestamps exist.

**Why Gold reads from Silver only?** Following Medallion Architecture principles, Gold benefits from Silver's data quality guarantees without re-implementing casting, deduplication, or SCD logic.