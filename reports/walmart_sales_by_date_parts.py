# walmart_sales_by_date_parts.py

# %% Cell 1 — Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
import warnings
import os
from connection import get_dataframe

print("✅ Libraries loaded")

# %% Cell 2 — Load data (run once)
df_raw = get_dataframe("""
    SELECT
        STORE_DATE,
        SALES_YEAR,
        SALES_MONTH,
        MONTH_NAME,
        WEEK_OF_YEAR,
        YEAR_MONTH,
        ISHOLIDAY,
        TOTAL_SALES,
        AVG_WEEKLY_SALES,
        NUM_STORES
    FROM WALMART_DB.GOLD.WALMART_SALES_BY_DATE_PARTS
    ORDER BY STORE_DATE
""")

print(f"✅ Data loaded: {len(df_raw)} rows")
print(f"   Years: {sorted(df_raw['SALES_YEAR'].unique())}")
print(f"   Date range: {df_raw['STORE_DATE'].min()} → {df_raw['STORE_DATE'].max()}")

# %% Cell 3 — Transform and chart
df = df_raw.copy()

# Convert types
df['TOTAL_SALES']      = df['TOTAL_SALES'].astype(float)
df['AVG_WEEKLY_SALES'] = df['AVG_WEEKLY_SALES'].astype(float)
df['SALES_YEAR']       = df['SALES_YEAR'].astype(int)
df['SALES_MONTH']      = df['SALES_MONTH'].astype(int)
df['STORE_DATE']       = pd.to_datetime(df['STORE_DATE'])
df['ISHOLIDAY']        = df['ISHOLIDAY'].apply(
    lambda x: 'TRUE' if str(x).upper() in ('TRUE', '1', 'YES') else 'FALSE'
)
df['TOTAL_SALES_M']    = df['TOTAL_SALES'] / 1e6

# -------------------------------------------------------
# Derived datasets
# -------------------------------------------------------
years         = sorted(df['SALES_YEAR'].unique())
month_order   = ['Jan','Feb','Mar','Apr','May','Jun',
                 'Jul','Aug','Sep','Oct','Nov','Dec']

# One color per year
year_colors   = {
    2010: '#1F77B4',   # blue
    2011: '#FF7F0E',   # orange
    2012: '#2CA02C'    # green
}

# Monthly aggregation across all years
df_monthly = (
    df.groupby(['SALES_MONTH', 'MONTH_NAME']) \
    .agg(
        TOTAL_SALES    = ('TOTAL_SALES_M', 'sum'),
        AVG_WEEKLY     = ('AVG_WEEKLY_SALES', 'mean')
    ) \
    .reset_index() \
    .sort_values('SALES_MONTH')
)

# Year over year — weekly totals per year
df_yoy = df.copy()
df_yoy['WEEK_NUM'] = df_yoy.groupby('SALES_YEAR').cumcount() + 1

# Holiday weeks
df_holidays = df[df['ISHOLIDAY'] == 'TRUE']

# Monthly holiday vs non-holiday avg
df_holiday_monthly = (
    df.groupby(['SALES_MONTH', 'MONTH_NAME', 'ISHOLIDAY']) \
    .agg(AVG_WEEKLY = ('AVG_WEEKLY_SALES', 'mean')) \
    .reset_index() \
    .sort_values('SALES_MONTH')
)

# -------------------------------------------------------
# Figure layout 2x2
# -------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(24, 14))
fig.patch.set_facecolor('white')
fig.suptitle('Walmart Weekly Sales by Date — Time Series Analysis',
             fontsize=18, fontweight='bold', y=1.01)

ax1 = axes[0, 0]   # Time series
ax2 = axes[0, 1]   # Year over year
ax3 = axes[1, 0]   # Monthly bar
ax4 = axes[1, 1]   # Holiday overlay

# -------------------------------------------------------
# Chart 1: Time series — Total sales over time
#          with holiday markers overlaid
# -------------------------------------------------------
ax1.plot(
    df['STORE_DATE'],
    df['TOTAL_SALES_M'],
    color='steelblue',
    linewidth=1.2,
    label='Weekly Total Sales'
)

# Shade holiday weeks
for _, row in df_holidays.iterrows():
    ax1.axvline(
        x=row['STORE_DATE'],
        color='red',
        alpha=0.3,
        linewidth=1.5,
        linestyle='--'
    )

# Add year boundary lines
for year in years[1:]:
    ax1.axvline(
        x=pd.Timestamp(f'{year}-01-01'),
        color='grey',
        alpha=0.4,
        linewidth=1,
        linestyle=':'
    )
    ax1.text(
        pd.Timestamp(f'{year}-01-01'),
        df['TOTAL_SALES_M'].max() * 0.95,
        str(year),
        fontsize=8, color='grey', ha='left'
    )

ax1.set_title('Total Weekly Sales Over Time\n(red dashes = holiday weeks)',
              fontsize=12, fontweight='bold')
ax1.set_xlabel('Date', fontsize=10)
ax1.set_ylabel('Total Sales ($M)', fontsize=10)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.0f}M'))
ax1.tick_params(axis='x', rotation=45, labelsize=8)
ax1.set_facecolor('white')
ax1.legend(fontsize=9)

# -------------------------------------------------------
# Chart 2: Year over year comparison
#          One line per year, x-axis = week number
# -------------------------------------------------------
for year in years:
    df_year = df_yoy[df_yoy['SALES_YEAR'] == year].sort_values('WEEK_NUM')
    ax2.plot(
        df_year['WEEK_NUM'],
        df_year['TOTAL_SALES_M'],
        color=year_colors.get(year, 'grey'),
        linewidth=1.5,
        label=str(year),
        alpha=0.85
    )

ax2.set_title('Year over Year Weekly Sales Comparison',
              fontsize=12, fontweight='bold')
ax2.set_xlabel('Week Number', fontsize=10)
ax2.set_ylabel('Total Sales ($M)', fontsize=10)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.0f}M'))
ax2.tick_params(axis='x', labelsize=8)
ax2.set_facecolor('white')
ax2.legend(title='Year', fontsize=9)

# -------------------------------------------------------
# Chart 3: Monthly bar — avg weekly sales by month
# -------------------------------------------------------
month_labels = df_monthly['MONTH_NAME'].tolist()
x3           = np.arange(len(month_labels))

bars3 = ax3.bar(
    x3,
    df_monthly['AVG_WEEKLY'],
    color='steelblue',
    edgecolor='white',
    width=0.6
)

# Value labels
for bar in bars3:
    ax3.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f'${bar.get_height():,.0f}',
        ha='center', va='bottom', fontsize=7.5
    )

ax3.set_title('Avg Weekly Sales by Month (All Years)',
              fontsize=12, fontweight='bold')
ax3.set_xlabel('Month', fontsize=10)
ax3.set_ylabel('Avg Weekly Sales ($)', fontsize=10)
ax3.set_xticks(x3)
ax3.set_xticklabels(month_labels, fontsize=9)
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax3.set_facecolor('white')

# -------------------------------------------------------
# Chart 4: Holiday vs non-holiday by month
# -------------------------------------------------------
df_h_false = df_holiday_monthly[df_holiday_monthly['ISHOLIDAY'] == 'FALSE'].sort_values('SALES_MONTH')
df_h_true  = df_holiday_monthly[df_holiday_monthly['ISHOLIDAY'] == 'TRUE'].sort_values('SALES_MONTH')

# Only months that have holiday data
holiday_months = df_h_true['SALES_MONTH'].tolist()
x4             = np.arange(len(holiday_months))
width4         = 0.35

false_vals = []
true_vals  = []
labels4    = []

for m in holiday_months:
    false_row = df_h_false[df_h_false['SALES_MONTH'] == m]
    true_row  = df_h_true[df_h_true['SALES_MONTH'] == m]
    false_vals.append(float(false_row['AVG_WEEKLY'].values[0]) if len(false_row) > 0 else 0)
    true_vals.append(float(true_row['AVG_WEEKLY'].values[0]))
    labels4.append(true_row['MONTH_NAME'].values[0])

bars4a = ax4.bar(x4 - width4/2, false_vals, width4,
                 label='Non-Holiday', color='#1F77B4', edgecolor='white')
bars4b = ax4.bar(x4 + width4/2, true_vals,  width4,
                 label='Holiday',     color='#555555', edgecolor='white')

# Value labels
for bar in bars4a:
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
             f'${bar.get_height():,.0f}',
             ha='center', va='bottom', fontsize=7, color='#1F77B4')
for bar in bars4b:
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
             f'${bar.get_height():,.0f}',
             ha='center', va='bottom', fontsize=7, color='#555555')

ax4.set_title('Holiday vs Non-Holiday Avg Weekly Sales by Month',
              fontsize=12, fontweight='bold')
ax4.set_xlabel('Month', fontsize=10)
ax4.set_ylabel('Avg Weekly Sales ($)', fontsize=10)
ax4.set_xticks(x4)
ax4.set_xticklabels(labels4, fontsize=9)
ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax4.legend(fontsize=9)
ax4.set_facecolor('white')

# -------------------------------------------------------
# Save and show
# -------------------------------------------------------
warnings.filterwarnings('ignore', message='This figure includes Axes')
os.makedirs('charts', exist_ok=True)
plt.tight_layout()
plt.savefig('charts/walmart_sales_by_date_parts.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print("✅ Chart saved to charts/walmart_sales_by_date_parts.png")
# %%
