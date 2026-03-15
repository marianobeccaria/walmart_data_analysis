# walmart_economic_factors.py

# %% Cell 1 — Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.cm as cm
import warnings
import os
from connection import get_dataframe

print("✅ Libraries loaded")

# %% Cell 2 — Load data (run once)
df_raw = get_dataframe("""
    SELECT
        STORE_ID,
        STORE_DATE,
        SALES_YEAR,
        SALES_MONTH,
        AVG_WEEKLY_SALES,
        AVG_TEMPERATURE,
        AVG_FUEL_PRICE,
        AVG_CPI,
        AVG_UNEMPLOYMENT
    FROM WALMART_DB.GOLD.WALMART_ECONOMIC_FACTORS
    ORDER BY STORE_DATE, STORE_ID
""")

print(f"✅ Data loaded: {len(df_raw)} rows")
print(f"   Date range: {df_raw['STORE_DATE'].min()} → {df_raw['STORE_DATE'].max()}")
print(f"   Years: {sorted(df_raw['SALES_YEAR'].unique())}")

# %% Cell 3 — Transform and chart
df = df_raw.copy()

# Convert types
num_cols = ['AVG_WEEKLY_SALES', 'AVG_TEMPERATURE', 'AVG_FUEL_PRICE',
            'AVG_CPI', 'AVG_UNEMPLOYMENT']
df[num_cols]     = df[num_cols].astype(float)
df['STORE_ID']   = df['STORE_ID'].astype(int)
df['SALES_YEAR'] = df['SALES_YEAR'].astype(int)
df['STORE_DATE'] = pd.to_datetime(df['STORE_DATE'])

# -------------------------------------------------------
# Colors — one per year
# -------------------------------------------------------
year_colors = {
    2010: '#1F77B4',   # blue
    2011: '#FF7F0E',   # orange
    2012: '#2CA02C'    # green
}

years = sorted(df['SALES_YEAR'].unique())

# -------------------------------------------------------
# Aggregated datasets
# -------------------------------------------------------

# Weekly avg across all stores per date — for time series
df_weekly = (
    df.groupby(['STORE_DATE', 'SALES_YEAR'])
    .agg(
        AVG_WEEKLY_SALES  = ('AVG_WEEKLY_SALES', 'mean'),
        AVG_TEMPERATURE   = ('AVG_TEMPERATURE',  'mean'),
        AVG_FUEL_PRICE    = ('AVG_FUEL_PRICE',   'mean'),
        AVG_UNEMPLOYMENT  = ('AVG_UNEMPLOYMENT', 'mean'),
        AVG_CPI           = ('AVG_CPI',          'mean')
    )
    .reset_index()
    .sort_values('STORE_DATE')
)

# Monthly fuel price trend
df_fuel = (
    df.groupby(['SALES_YEAR', 'SALES_MONTH'])
    .agg(AVG_FUEL_PRICE = ('AVG_FUEL_PRICE', 'mean'))
    .reset_index()
    .sort_values(['SALES_YEAR', 'SALES_MONTH'])
)
df_fuel['MONTH_NUM'] = (df_fuel['SALES_YEAR'] - 2010) * 12 + df_fuel['SALES_MONTH']

# -------------------------------------------------------
# Figure 2x2
# -------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(22, 14))
fig.patch.set_facecolor('white')
fig.suptitle('Walmart Weekly Sales vs Economic Factors',
             fontsize=18, fontweight='bold', y=1.01)

ax1 = axes[0, 0]   # Temperature vs Sales (line)
ax2 = axes[0, 1]   # Fuel Price vs Sales (scatter)
ax3 = axes[1, 0]   # Fuel Price trend by year (line)
ax4 = axes[1, 1]   # Unemployment vs Sales (scatter)

# -------------------------------------------------------
# Chart 1: Weekly Sales vs Temperature — dual axis line
# -------------------------------------------------------
ax1b = ax1.twinx()   # second y-axis for temperature

for year in years:
    df_y = df_weekly[df_weekly['SALES_YEAR'] == year].sort_values('STORE_DATE')
    ax1.plot(
        df_y['STORE_DATE'],
        df_y['AVG_WEEKLY_SALES'],
        color     = year_colors[year],
        linewidth = 1.5,
        label     = f'Sales {year}'
    )
    ax1b.plot(
        df_y['STORE_DATE'],
        df_y['AVG_TEMPERATURE'],
        color     = year_colors[year],
        linewidth = 1,
        linestyle = '--',
        alpha     = 0.5,
        label     = f'Temp {year}'
    )

ax1.set_title('Weekly Sales vs Temperature Over Time',
              fontsize=12, fontweight='bold')
ax1.set_xlabel('Date', fontsize=10)
ax1.set_ylabel('Avg Weekly Sales ($)', fontsize=10, color='black')
ax1b.set_ylabel('Avg Temperature (°F)', fontsize=10, color='grey')
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax1.tick_params(axis='x', rotation=45, labelsize=8)
ax1.set_facecolor('white')

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1b.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2,
           fontsize=7, loc='upper right', ncol=2)

# -------------------------------------------------------
# Chart 2: Fuel Price vs Weekly Sales — scatter
# -------------------------------------------------------
for year in years:
    df_y = df[df['SALES_YEAR'] == year]
    ax2.scatter(
        df_y['AVG_FUEL_PRICE'],
        df_y['AVG_WEEKLY_SALES'],
        color  = year_colors[year],
        alpha  = 0.4,
        s      = 15,
        label  = str(year)
    )

# Add trend line across all years
z = np.polyfit(df['AVG_FUEL_PRICE'], df['AVG_WEEKLY_SALES'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['AVG_FUEL_PRICE'].min(),
                     df['AVG_FUEL_PRICE'].max(), 100)
ax2.plot(x_line, p(x_line),
         color='red', linewidth=1.5,
         linestyle='--', label='Trend')

ax2.set_title('Weekly Sales vs Fuel Price',
              fontsize=12, fontweight='bold')
ax2.set_xlabel('Avg Fuel Price ($)', fontsize=10)
ax2.set_ylabel('Avg Weekly Sales ($)', fontsize=10)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.2f}'))
ax2.legend(title='Year', fontsize=9)
ax2.set_facecolor('white')
ax2.grid(linestyle='--', alpha=0.3)

# -------------------------------------------------------
# Chart 3: Fuel Price trend by year — line
# -------------------------------------------------------
month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
               7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

for year in years:
    df_y = df_fuel[df_fuel['SALES_YEAR'] == year].sort_values('SALES_MONTH')
    ax3.plot(
        df_y['SALES_MONTH'],
        df_y['AVG_FUEL_PRICE'],
        color     = year_colors[year],
        linewidth = 2,
        marker    = 'o',
        markersize= 5,
        label     = str(year)
    )

ax3.set_title('Fuel Price Trend by Year',
              fontsize=12, fontweight='bold')
ax3.set_xlabel('Month', fontsize=10)
ax3.set_ylabel('Avg Fuel Price ($)', fontsize=10)
ax3.set_xticks(range(1, 13))
ax3.set_xticklabels([month_names[m] for m in range(1, 13)], fontsize=8)
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.2f}'))
ax3.legend(title='Year', fontsize=9)
ax3.set_facecolor('white')
ax3.grid(linestyle='--', alpha=0.3)

# -------------------------------------------------------
# Chart 4: Unemployment vs Weekly Sales — scatter
# -------------------------------------------------------
for year in years:
    df_y = df[df['SALES_YEAR'] == year]
    ax4.scatter(
        df_y['AVG_UNEMPLOYMENT'],
        df_y['AVG_WEEKLY_SALES'],
        color  = year_colors[year],
        alpha  = 0.4,
        s      = 15,
        label  = str(year)
    )

# Trend line
z2 = np.polyfit(df['AVG_UNEMPLOYMENT'], df['AVG_WEEKLY_SALES'], 1)
p2 = np.poly1d(z2)
x_line2 = np.linspace(df['AVG_UNEMPLOYMENT'].min(),
                      df['AVG_UNEMPLOYMENT'].max(), 100)
ax4.plot(x_line2, p2(x_line2),
         color='red', linewidth=1.5,
         linestyle='--', label='Trend')

ax4.set_title('Weekly Sales vs Unemployment Rate',
              fontsize=12, fontweight='bold')
ax4.set_xlabel('Avg Unemployment Rate (%)', fontsize=10)
ax4.set_ylabel('Avg Weekly Sales ($)', fontsize=10)
ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax4.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f}%'))
ax4.legend(title='Year', fontsize=9)
ax4.set_facecolor('white')
ax4.grid(linestyle='--', alpha=0.3)

# -------------------------------------------------------
# Save and show
# -------------------------------------------------------
warnings.filterwarnings('ignore', message='This figure includes Axes')
os.makedirs('charts', exist_ok=True)
plt.tight_layout()
plt.savefig('charts/walmart_economic_factors.png',
            dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print("✅ Chart saved to charts/walmart_economic_factors.png")
# %%
