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
│  dbt models     │  and fact tables (SCD1 / SCD2)
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
├── packages.yml                 # dbt packages (dbt_utils)
├── profiles.yml                 # Snowflake connection profile
│
├── macros/
│   ├── macros_copy_csv.sql      # Reusable COPY INTO macro
│   ├── load_all_bronze.sql      # Orchestrates all 3 bronze loads
│   └── generate_schema_name.sql # Schema naming override
│
├── models/
│   ├── sources.yml              # Bronze table source definitions
│   │
│   ├── silver/
│   │   ├── schema.yml           # Silver model definitions & tests
│   │   ├── walmart_date_dim.sql
│   │   ├── walmart_store_dim.sql
│   │   └── walmart_fact_table.sql
│   │
│   └── gold/
│       ├── schema.yml
│       ├── walmart_sales_by_store.sql
│       ├── walmart_sales_by_dept.sql
│       ├── walmart_sales_by_date_parts.sql
│       ├── walmart_sales_by_storetype_month.sql
│       ├── walmart_markdown_by_year_store.sql
│       ├── walmart_holiday_impact.sql
│       └── walmart_economic_factors.sql
│
├── snapshots/                   # (deprecated — replaced by incremental model)
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
- dbt Cloud account
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

#### `walmart_fact_table` — SCD Type 2
Central fact table containing weekly sales and economic measures. Implements SCD2 versioning so historical records are preserved when data changes.

| Column | Type | Description |
|--------|------|-------------|
| SNAPSHOT_KEY | VARCHAR | Surrogate unique key (STORE_ID + DEPT_ID + DATE) |
| STORE_ID | INT | Foreign key to store_dim |
| DEPT_ID | INT | Foreign key to store_dim |
| DATE_ID | INT | Foreign key to date_dim |
| STORE_DATE | DATE | Week ending date |
| STORE_WEEKLY_SALES | DECIMAL | Weekly sales amount in dollars |
| FUEL_PRICE | DECIMAL | Regional fuel price |
| TEMPERATURE | DECIMAL | Average weekly temperature (°F) |
| CPI | DECIMAL | Consumer Price Index |
| UNEMPLOYMENT | DECIMAL | Regional unemployment rate |
| MARKDOWN1-5 | DECIMAL | Promotional markdown amounts |
| VRSN_START_DATE | TIMESTAMP | When this version became active |
| VRSN_END_DATE | TIMESTAMP | When this version was superseded (NULL = current) |
| INSERT_DATE | TIMESTAMP | Record creation timestamp |
| UPDATE_DATE | TIMESTAMP | Record last updated timestamp |

**SCD2** means when a row changes (e.g. sales corrected), the old row gets a `VRSN_END_DATE` and a new row is inserted with `VRSN_END_DATE = NULL`. This preserves the full history of changes.

To query only current active records:
```sql
SELECT * FROM WALMART_DB.SILVER.WALMART_FACT_TABLE
WHERE VRSN_END_DATE IS NULL;
```

---

## Gold Layer

**Schema:** `WALMART_DB.GOLD`

The Gold layer contains pre-aggregated, report-ready tables. All Gold models read from Silver (never directly from Bronze) and are materialized as tables for fast query performance.

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

Shows total sales per store colored by store type (A/B/C). Helps identify which stores and store types drive the most revenue. Type A (large format) stores consistently outperform Type B and C stores.

---

### 2. `walmart_sales_by_dept.py`
**Requirement:** Weekly sales by department

Four-panel dashboard showing: total sales by department/store, avg weekly sales, side-by-side comparison, and a Min/Avg/Max grouped bar chart. Department 92 is consistently the top performer across stores.

---

### 3. `walmart_holiday_impact.py`
**Requirement:** Weekly sales by store and holiday

Three-panel layout with a pie chart showing holiday vs non-holiday sales share, a grand total KPI card, a holiday premium KPI card, and a grouped bar chart comparing holiday vs non-holiday sales per store. Holiday weeks show approximately 7% higher average weekly sales than non-holiday weeks.

---

### 4. `walmart_sales_by_date_parts.py`
**Requirement:** Weekly sales by year, month and day

Four-panel time series dashboard: full weekly trend with holiday markers, year-over-year comparison lines, monthly seasonality bar chart, and holiday vs non-holiday comparison by month. Shows clear seasonality peaks in November/December driven by holiday shopping.

---

### 5. `walmart_sales_by_storetype_month.py`
**Requirement:** Weekly sales by store type and month

Two-panel layout with a line chart showing monthly sales trends per store type and a summary table with monthly totals for each store type. Type A stores show significantly higher absolute sales but all types follow similar seasonal patterns.

---

### 6. `walmart_markdown_by_year_store.py`
**Requirement:** Markdown sales by year and store

Grouped bar chart showing markdown amounts by type (MD1-MD5) for each year. No markdown data exists for 2010 — Walmart began recording markdowns in 2011. Markdown activity increased significantly from 2011 to 2012 with Markdown 3 and Markdown 5 showing the largest growth.

---

### 7. `walmart_economic_factors.py`
**Requirement:** Weekly sales by CPI, temperature, fuel price, and unemployment

Four-panel chart with scatter plots and line charts examining the relationship between weekly sales and key economic indicators. Notable findings: fuel price shows a positive correlation with sales (both rose together as the economy recovered post-2009), while unemployment shows a negative correlation (higher unemployment correlates with lower spending).

> **Note:** Correlation does not imply causation. External economic conditions (post-recession recovery) likely influenced both sales and these factors simultaneously.

---

## How to Run

### Full Pipeline (from scratch)

```bash
# Step 1: Load Bronze tables from S3
dbt run-operation load_all_bronze

# Step 2: Build Silver dimension and fact tables
dbt run --select silver --full-refresh

# Step 3: Build Gold aggregation tables
dbt run --select gold

# Step 4: Run data quality tests
dbt test

# Step 5: Generate documentation
dbt docs generate
dbt docs serve
```

### Incremental Run (new data loaded to S3)

```bash
# Reload Bronze with new data
dbt run-operation load_all_bronze

# Incrementally update Silver (new rows only)
dbt run --select silver

# Rebuild Gold
dbt run --select gold
```

### Generate Python Charts

```bash
cd reports
conda activate walmart_env

python walmart_sales_by_store.py
python walmart_sales_by_dept.py
python walmart_holiday_impact.py
python walmart_sales_by_date_parts.py
python walmart_sales_by_storetype_month.py
python walmart_markdown_by_year_store.py
python walmart_economic_factors.py
```

Charts are saved to `reports/charts/`.

---

## dbt Commands Reference

| Command | Purpose |
|---------|---------|
| `dbt run` | Build all models |
| `dbt run --select model_name` | Build a specific model |
| `dbt run --full-refresh` | Rebuild all models from scratch |
| `dbt test` | Run all data quality tests |
| `dbt run-operation load_all_bronze` | Load raw CSV data into Bronze |
| `dbt compile` | Generate SQL without executing |
| `dbt docs generate && dbt docs serve` | Build and view documentation |
| `dbt source freshness` | Check Bronze table freshness |

---

## Key Design Decisions

**Why VARCHAR in Bronze?** The source CSVs contain `NA` values in markdown columns. Using `VARCHAR` for all Bronze columns ensures `COPY INTO` never fails due to type casting errors. All casting happens in Silver using `TRY_CAST()` which returns `NULL` instead of erroring on bad values.

**Why SCD2 for the fact table?** Sales data can be retroactively corrected. SCD2 preserves the original record and inserts a new version, allowing historical analysis to reflect what the data looked like at any point in time.

**Why dbt incremental instead of snapshot?** dbt-fusion (v2 preview) has known issues with snapshot deduplication. The incremental model with `QUALIFY ROW_NUMBER()` provides the same SCD2 behavior with more explicit control and reliable deduplication.

**Why Gold reads from Silver only?** Following Medallion Architecture principles, each layer builds on the previous one. Gold models benefit from Silver's data quality guarantees (proper types, deduplication, SCD versioning) without needing to re-implement that logic.