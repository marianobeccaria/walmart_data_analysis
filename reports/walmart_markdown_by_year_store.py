# walmart_markdown_by_year_store.py

# %% Cell 1 — Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import warnings
import os
from connection import get_dataframe

print("✅ Libraries loaded")

# %% Cell 2 — Load data (run once)
df_raw = get_dataframe("""
    SELECT
        STORE_ID,
        STORE_TYPE,
        SALES_YEAR,
        TOTAL_SALES,
        TOTAL_MARKDOWN1,
        TOTAL_MARKDOWN2,
        TOTAL_MARKDOWN3,
        TOTAL_MARKDOWN4,
        TOTAL_MARKDOWN5,
        TOTAL_ALL_MARKDOWNS
    FROM WALMART_DB.GOLD.WALMART_MARKDOWN_BY_YEAR_STORE
    ORDER BY SALES_YEAR, STORE_ID
""")

print(f"✅ Data loaded: {len(df_raw)} rows")
print(f"   Years: {sorted(df_raw['SALES_YEAR'].unique())}")
print(f"   Stores: {df_raw['STORE_ID'].nunique()}")

# %% Cell 3 — Transform and chart
df = df_raw.copy()

# Convert types
md_cols = ['TOTAL_SALES', 'TOTAL_MARKDOWN1', 'TOTAL_MARKDOWN2',
           'TOTAL_MARKDOWN3', 'TOTAL_MARKDOWN4', 'TOTAL_MARKDOWN5',
           'TOTAL_ALL_MARKDOWNS']
df[md_cols]      = df[md_cols].astype(float)
df['STORE_ID']   = df['STORE_ID'].astype(int)
df['SALES_YEAR'] = df['SALES_YEAR'].astype(int)

# -------------------------------------------------------
# Colors — one per markdown type
# -------------------------------------------------------
md_colors = {
    'Markdown 1': '#1F77B4',   # blue
    'Markdown 2': '#FF7F0E',   # orange
    'Markdown 3': '#2CA02C',   # green
    'Markdown 4': '#D62728',   # red
    'Markdown 5': '#9467BD'    # purple
}

# -------------------------------------------------------
# Aggregate by year — sum all markdowns across stores
# -------------------------------------------------------
df_yearly = (
    df.groupby('SALES_YEAR')
    .agg(
        MD1 = ('TOTAL_MARKDOWN1', 'sum'),
        MD2 = ('TOTAL_MARKDOWN2', 'sum'),
        MD3 = ('TOTAL_MARKDOWN3', 'sum'),
        MD4 = ('TOTAL_MARKDOWN4', 'sum'),
        MD5 = ('TOTAL_MARKDOWN5', 'sum'),
        TOTAL_ALL = ('TOTAL_ALL_MARKDOWNS', 'sum'),
        TOTAL_SALES = ('TOTAL_SALES', 'sum')
    )
    .reset_index()
)

# Convert to millions
for col in ['MD1','MD2','MD3','MD4','MD5','TOTAL_ALL','TOTAL_SALES']:
    df_yearly[f'{col}_M'] = df_yearly[col] / 1e6

# # -------------------------------------------------------
# # Figure — single focused stacked bar chart
# # with total annotation and pct of sales
# # -------------------------------------------------------
# fig, ax = plt.subplots(figsize=(12, 7))
# fig.patch.set_facecolor('white')
# fig.suptitle('Markdown Sales by Year and Store\n(2011-2012 only — no markdown data in 2010)',
#              fontsize=16, fontweight='bold', y=1.02)

# years  = df_yearly['SALES_YEAR'].tolist()
# x      = np.arange(len(years))
# width  = 0.5

# # Stack bars MD1 through MD5
# md_keys   = ['MD1_M', 'MD2_M', 'MD3_M', 'MD4_M', 'MD5_M']
# md_labels = list(md_colors.keys())
# bottoms   = np.zeros(len(years))

# bars_list = []
# for md_key, md_label, color in zip(md_keys, md_labels, md_colors.values()):
#     vals = df_yearly[md_key].values
#     bars = ax.bar(
#         x,
#         vals,
#         width,
#         bottom   = bottoms,
#         label    = md_label,
#         color    = color,
#         edgecolor= 'white',
#         linewidth= 0.8
#     )
#     bars_list.append((bars, vals))

#     # Label each segment if large enough
#     for i, (bar, val) in enumerate(zip(bars, vals)):
#         if val > 20:   # only label if segment > $20M
#             ax.text(
#                 bar.get_x() + bar.get_width() / 2,
#                 bottoms[i] + val / 2,
#                 f'${val:,.0f}M',
#                 ha='center', va='center',
#                 fontsize=8, color='white', fontweight='bold'
#             )
#     bottoms += vals

# # Total label on top of each bar
# for i, row in df_yearly.iterrows():
#     total_m   = row['TOTAL_ALL_M']
#     pct_sales = (row['TOTAL_ALL'] / row['TOTAL_SALES']) * 100
#     ax.text(
#         x[i],
#         bottoms[i] + 5,
#         f'Total: ${total_m:,.0f}M\n({pct_sales:.1f}% of sales)',
#         ha='center', va='bottom',
#         fontsize=10, fontweight='bold', color='black'
#     )

# # Year over year change annotation
# if len(df_yearly) == 2:
#     yoy_change = ((df_yearly['TOTAL_ALL'].iloc[1] -
#                    df_yearly['TOTAL_ALL'].iloc[0]) /
#                    df_yearly['TOTAL_ALL'].iloc[0]) * 100
#     ax.annotate(
#         f'+{yoy_change:.0f}% YoY',
#         xy     = (x[1], bottoms[1] * 0.5),
#         xytext = (x[1] + 0.35, bottoms[1] * 0.6),
#         fontsize   = 11,
#         fontweight = 'bold',
#         color      = 'darkred',
#         bbox       = dict(boxstyle='round,pad=0.3',
#                           facecolor='lightyellow',
#                           edgecolor='darkred'),
#         arrowprops = dict(arrowstyle='->', color='darkred', lw=1.5)
#     )

# ax.set_title('Total Markdown by Year — Breakdown by Markdown Type',
#              fontsize=13, fontweight='bold')
# ax.set_xlabel('Year', fontsize=11)
# ax.set_ylabel('Total Markdown ($M)', fontsize=11)
# ax.set_xticks(x)
# ax.set_xticklabels([str(y) for y in years], fontsize=11)
# ax.yaxis.set_major_formatter(
#     mticker.FuncFormatter(lambda v, _: f'${v:,.0f}M')
# )
# ax.legend(
#     title     = 'Markdown Type',
#     fontsize  = 10,
#     loc       = 'upper left'
# )
# ax.set_facecolor('white')
# ax.grid(axis='y', linestyle='--', alpha=0.4)

# -------------------------------------------------------
# Figure — grouped bar chart
# -------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor('white')
fig.suptitle('Markdown Sales by Year — Breakdown by Markdown Type',
             fontsize=16, fontweight='bold', y=1.02)

years     = df_yearly['SALES_YEAR'].tolist()
md_keys   = ['MD1_M', 'MD2_M', 'MD3_M', 'MD4_M', 'MD5_M']
md_labels = list(md_colors.keys())
n_mds     = len(md_keys)
n_years   = len(years)

# Calculate bar positions
width     = 0.15                              # width of each bar
x         = np.arange(n_years)               # one group per year
offsets   = np.linspace(
    -(n_mds - 1) / 2 * width,
     (n_mds - 1) / 2 * width,
    n_mds
)

for md_key, md_label, color, offset in zip(md_keys, md_labels,
                                            md_colors.values(), offsets):
    vals = df_yearly[md_key].values
    bars = ax.bar(
        x + offset,
        vals,
        width,
        label     = md_label,
        color     = color,
        edgecolor = 'white',
        linewidth = 0.8
    )

    # Value labels on top of each bar
    for bar, val in zip(bars, vals):
        if val > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 2,
                f'${val:,.0f}M',
                ha='center', va='bottom',
                fontsize=7, color=color,
                fontweight='bold',
                rotation=90
            )

# Total markdown annotation below x-axis labels
# for i, row in df_yearly.iterrows():
#     total_m   = row['TOTAL_ALL_M']
#     pct_sales = (row['TOTAL_ALL'] / row['TOTAL_SALES']) * 100 if row['TOTAL_SALES'] > 0 else 0
#     label     = f'Total: ${total_m:,.0f}M\n({pct_sales:.1f}% of sales)' if total_m > 0 else 'No markdown\ndata'
#     ax.text(
#         x[i],
#         -ax.get_ylim()[1] * 0.08,
#         label,
#         ha='center', va='top',
#         fontsize=9,
#         fontweight='bold',
#         color='black' if total_m > 0 else 'grey',
#         transform=ax.transData
#     )
    
for i, row in df_yearly.iterrows():
    total_m   = row['TOTAL_ALL_M']
    pct_sales = (row['TOTAL_ALL'] / row['TOTAL_SALES']) * 100 \
                if row['TOTAL_SALES'] > 0 else 0
    label     = f'Total: ${total_m:,.0f}M\n({pct_sales:.1f}% of sales)' \
                if total_m > 0 else 'No markdown\ndata'
    ax.annotate(
        label,
        xy         = (x[i], 0),
        xytext     = (x[i], -ax.get_ylim()[1] * 0.15),  # fixed % below zero
        ha         = 'center',
        va         = 'top',
        fontsize   = 9,
        fontweight = 'bold',
        color      = 'black' if total_m > 0 else 'grey',
        annotation_clip = False    # ← allows drawing outside plot area
    )

# -------------------------------------------------------
# YoY change annotation
# -------------------------------------------------------
years_with_data = df_yearly[df_yearly['TOTAL_ALL'] > 0]['SALES_YEAR'].tolist()
if len(years_with_data) >= 2:
    y1_idx = df_yearly[df_yearly['SALES_YEAR'] == years_with_data[0]].index[0]
    y2_idx = df_yearly[df_yearly['SALES_YEAR'] == years_with_data[1]].index[0]
    yoy_change = ((df_yearly.loc[y2_idx, 'TOTAL_ALL'] -
                   df_yearly.loc[y1_idx, 'TOTAL_ALL']) /
                   df_yearly.loc[y1_idx, 'TOTAL_ALL']) * 100
    ax.annotate(
        f'+{yoy_change:.0f}% YoY\n({years_with_data[0]}→{years_with_data[1]})',
        xy     = (x[y2_idx], df_yearly.loc[y2_idx, 'MD1_M']),
        xytext = (x[y2_idx] + 0.5, df_yearly.loc[y2_idx, 'MD1_M'] * 1.2),
        fontsize   = 10,
        fontweight = 'bold',
        color      = 'darkred',
        bbox       = dict(boxstyle='round,pad=0.3',
                          facecolor='lightyellow',
                          edgecolor='darkred'),
        arrowprops = dict(arrowstyle='->', color='darkred', lw=1.5)
    )

# -------------------------------------------------------
# Axis formatting
# -------------------------------------------------------
ax.set_xlabel('Year', fontsize=11, labelpad=50)
ax.set_ylabel('Total Markdown ($M)', fontsize=11)
ax.set_xticks(x)
ax.set_xticklabels([str(y) for y in years], fontsize=11)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: f'${v:,.0f}M')
)
ax.legend(title='Markdown Type', fontsize=10, loc='upper left')
ax.set_facecolor('white')
ax.grid(axis='y', linestyle='--', alpha=0.4)

# -------------------------------------------------------
# Save and show
# -------------------------------------------------------
warnings.filterwarnings('ignore', message='This figure includes Axes')
os.makedirs('charts', exist_ok=True)
plt.tight_layout()
plt.subplots_adjust(bottom=0.2)   # creates space below x-axis for labels

plt.savefig('charts/walmart_markdown_by_year_store.png',
            dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print("✅ Chart saved to charts/walmart_markdown_by_year_store.png")
print(f"   2011 total markdowns: ${df_yearly[df_yearly['SALES_YEAR']==2011]['TOTAL_ALL_M'].values[0]:,.0f}M")
print(f"   2012 total markdowns: ${df_yearly[df_yearly['SALES_YEAR']==2012]['TOTAL_ALL_M'].values[0]:,.0f}M")
# %%
