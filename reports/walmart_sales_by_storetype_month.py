# walmart_sales_by_storetype_month.py

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
        STORE_TYPE,
        SALES_YEAR,
        SALES_MONTH,
        YEAR_MONTH,
        AVG_WEEKLY_SALES,
        TOTAL_SALES,
        NUM_STORES
    FROM WALMART_DB.GOLD.WALMART_SALES_BY_STORETYPE_MONTH
    ORDER BY SALES_YEAR, SALES_MONTH, STORE_TYPE
""")

print(f"✅ Data loaded: {len(df_raw)} rows")
print(f"   Store types: {sorted(df_raw['STORE_TYPE'].unique())}")
print(f"   Years: {sorted(df_raw['SALES_YEAR'].unique())}")

# %% Cell 3 — Transform and chart
df = df_raw.copy()

# Convert types
df['TOTAL_SALES']      = df['TOTAL_SALES'].astype(float)
df['AVG_WEEKLY_SALES'] = df['AVG_WEEKLY_SALES'].astype(float)
df['SALES_YEAR']       = df['SALES_YEAR'].astype(int)
df['SALES_MONTH']      = df['SALES_MONTH'].astype(int)
df['TOTAL_SALES_B']    = df['TOTAL_SALES'] / 1e9   # billions for line chart

# -------------------------------------------------------
# Colors — one per store type
# -------------------------------------------------------
type_colors = {
    'A': '#1F77B4',   # blue
    'B': '#FF7F0E',   # orange
    'C': '#2CA02C'    # green
}

month_names = {
    1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr',
    5:'May', 6:'Jun', 7:'Jul', 8:'Aug',
    9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'
}

# -------------------------------------------------------
# Line chart data: monthly total sales per store type
# aggregated across all years
# -------------------------------------------------------
df_line = (
    df.groupby(['STORE_TYPE', 'SALES_MONTH'])
    .agg(TOTAL_SALES_M = ('TOTAL_SALES', lambda x: x.sum() / 1e6))
    .reset_index()
    .sort_values(['STORE_TYPE', 'SALES_MONTH'])
)

# -------------------------------------------------------
# Table data: pivot months x store types (all years combined)
# -------------------------------------------------------
df_table = (
    df.groupby(['SALES_MONTH', 'STORE_TYPE'])
    ['TOTAL_SALES']
    .sum()
    .reset_index()
)

df_pivot = df_table.pivot(
    index='SALES_MONTH',
    columns='STORE_TYPE',
    values='TOTAL_SALES'
).reset_index()

df_pivot['MONTH_NAME'] = df_pivot['SALES_MONTH'].map(month_names)
df_pivot = df_pivot.sort_values('SALES_MONTH')

# Add totals row
totals = pd.DataFrame({
    'SALES_MONTH': [99],
    'MONTH_NAME':  ['TOTAL'],
    'A': [df_pivot['A'].sum()],
    'B': [df_pivot['B'].sum()],
    'C': [df_pivot['C'].sum() if 'C' in df_pivot.columns else 0]
})
df_pivot = pd.concat([df_pivot, totals], ignore_index=True)

# -------------------------------------------------------
# Figure layout — line 2/3, table 1/3
# -------------------------------------------------------
fig = plt.figure(figsize=(24, 10))
fig.patch.set_facecolor('white')
fig.suptitle('Weekly Sales by Store Type and Month',
             fontsize=20, fontweight='bold', y=1.01)

gs = gridspec.GridSpec(
    1, 3,
    # width_ratios = [2, 2, 1],   # line chart takes 2/3, table takes 1/3
    # wspace       = 0.35
    width_ratios = [2, 2, 1.8],   # line chart takes 2/3, table takes 1/3
    wspace       = 0.2
)

ax_line  = fig.add_subplot(gs[0, :2])   # spans first 2 columns
ax_table = fig.add_subplot(gs[0, 2])    # last column

# -------------------------------------------------------
# Line chart — monthly sales trend per store type
# -------------------------------------------------------
months     = sorted(df_line['SALES_MONTH'].unique())
month_lbls = [month_names[m] for m in months]

for stype in ['A', 'B', 'C']:
    df_type = df_line[df_line['STORE_TYPE'] == stype].sort_values('SALES_MONTH')
    if len(df_type) == 0:
        continue
    ax_line.plot(
        df_type['SALES_MONTH'],
        df_type['TOTAL_SALES_M'],
        color     = type_colors[stype],
        linewidth = 2.5,
        marker    = 'o',
        markersize= 6,
        label     = f'Type {stype}'
    )
    # Label last point
    last = df_type.iloc[-1]
    ax_line.annotate(
        f'${last["TOTAL_SALES_M"]:,.0f}M',
        xy       = (last['SALES_MONTH'], last['TOTAL_SALES_M']),
        xytext   = (5, 0),
        textcoords = 'offset points',
        fontsize = 8,
        color    = type_colors[stype],
        fontweight = 'bold'
    )

ax_line.set_title('Total Sales by Store Type and Month (All Years Combined)',
                  fontsize=16, fontweight='bold')
ax_line.set_xlabel('Month', fontsize=11)
ax_line.set_ylabel('Total Sales ($M)', fontsize=11)
ax_line.set_xticks(months)
ax_line.set_xticklabels(month_lbls, fontsize=9)
ax_line.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f'${x:,.0f}M')
)
ax_line.legend(title='Store Type', fontsize=10)
ax_line.set_facecolor('white')
ax_line.grid(axis='y', linestyle='--', alpha=0.4)

# -------------------------------------------------------
# Table — Month | Type A | Type B | Type C
# -------------------------------------------------------
ax_table.axis('off')

# Build table data
col_labels  = ['Month', 'Type A ($M)', 'Type B ($M)', 'Type C ($M)']
table_data  = []

for _, row in df_pivot.iterrows():
    month_label = row['MONTH_NAME']
    a_val = f"${row['A']/1e6:,.0f}M" if pd.notna(row.get('A')) else '-'
    b_val = f"${row['B']/1e6:,.0f}M" if pd.notna(row.get('B')) else '-'
    c_val = f"${row['C']/1e6:,.0f}M" if pd.notna(row.get('C')) else '-'
    table_data.append([month_label, a_val, b_val, c_val])

# Draw table
table = ax_table.table(
    cellText    = table_data,
    colLabels   = col_labels,
    loc         = 'center',
    cellLoc     = 'center'
)
table.auto_set_font_size(False)
# table.set_fontsize(8.5)
# table.scale(1, 1.4)
table.set_fontsize(12)
table.scale(1.2, 1.8)

# Style header row
for col in range(4):
    table[0, col].set_facecolor('#2C3E50')
    table[0, col].set_text_props(color='white', fontweight='bold')

# Style totals row (last row)
total_row_idx = len(table_data)
for col in range(4):
    table[total_row_idx, col].set_facecolor('#ECF0F1')
    table[total_row_idx, col].set_text_props(fontweight='bold')

# Alternating row colors
for row_idx in range(1, len(table_data)):
    color = '#F8F9FA' if row_idx % 2 == 0 else 'white'
    for col in range(4):
        table[row_idx, col].set_facecolor(color)

# Color the store type columns header to match line chart
table[0, 1].set_facecolor(type_colors['A'])
table[0, 2].set_facecolor(type_colors['B'])
table[0, 3].set_facecolor(type_colors['C'])

ax_table.set_title('Monthly Sales by Store Type\n(All Years Combined)',
                   fontsize=16, fontweight='bold', pad=10)

# -------------------------------------------------------
# Save and show
# -------------------------------------------------------
warnings.filterwarnings('ignore', message='This figure includes Axes')
os.makedirs('charts', exist_ok=True)
plt.tight_layout()
plt.savefig('charts/walmart_sales_by_storetype_month.png',
            dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print("✅ Chart saved to charts/walmart_sales_by_storetype_month.png")
# %%
