# walmart_holiday_impact.py
# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import os
from connection import get_dataframe

# -------------------------------------------------------
# Data
# -------------------------------------------------------
# %%
df_raw = get_dataframe("""
    SELECT
        STORE_ID,
        STORE_TYPE,
        ISHOLIDAY,
        TOTAL_SALES,
        AVG_WEEKLY_SALES,
        WEEKS_OF_DATA
    FROM WALMART_DB.GOLD.WALMART_SALES_BY_STORE
    ORDER BY STORE_ID, ISHOLIDAY
""")

# Convert types
# %%

# Always work from df_raw so re-running never corrupts data
df = df_raw.copy()

numeric_cols = ['TOTAL_SALES', 'AVG_WEEKLY_SALES', 'WEEKS_OF_DATA']
df[numeric_cols]    = df[numeric_cols].astype(float)
df['STORE_ID']      = df['STORE_ID'].astype(int)
df['ISHOLIDAY']     = df['ISHOLIDAY'].apply(lambda x: 'TRUE' if x else 'FALSE')
df['TOTAL_SALES_M'] = df['TOTAL_SALES'] / 1e6

# -------------------------------------------------------
# Summary metrics
# -------------------------------------------------------
grand_total      = df['TOTAL_SALES'].sum()
holiday_total    = df[df['ISHOLIDAY'] == 'TRUE']['TOTAL_SALES'].sum()
nonholiday_total = df[df['ISHOLIDAY'] == 'FALSE']['TOTAL_SALES'].sum()
holiday_avg      = df[df['ISHOLIDAY'] == 'TRUE']['AVG_WEEKLY_SALES'].mean()
nonholiday_avg   = df[df['ISHOLIDAY'] == 'FALSE']['AVG_WEEKLY_SALES'].mean()
pct_diff         = ((holiday_avg - nonholiday_avg) / nonholiday_avg) * 100

# -------------------------------------------------------
# Colors
# -------------------------------------------------------
COLOR_NONHOLIDAY = '#1F77B4'   # blue
COLOR_HOLIDAY    = '#555555'   # grey

# -------------------------------------------------------
# Figure layout
# -------------------------------------------------------
fig = plt.figure(figsize=(22, 12))
fig.patch.set_facecolor('white')
fig.suptitle('Weekly Sales by Store and Holiday',
             fontsize=20, fontweight='bold', y=1.01)

gs = gridspec.GridSpec(
    3, 2,
    width_ratios  = [1, 3],
    height_ratios = [1.5, 1, 1],
    hspace        = 0.5,
    wspace        = 0.3
)

ax_pie = fig.add_subplot(gs[0, 0])
ax_kpi = fig.add_subplot(gs[1, 0])
ax_avg = fig.add_subplot(gs[2, 0])
ax_bar = fig.add_subplot(gs[:, 1])

# -------------------------------------------------------
# Panel 1 — Pie chart
# -------------------------------------------------------
ax_pie.set_facecolor('white')

wedges, texts, autotexts = ax_pie.pie(
    [nonholiday_total, holiday_total],
    colors     = [COLOR_NONHOLIDAY, COLOR_HOLIDAY],
    explode    = (0.03, 0.03),
    autopct    = '%1.1f%%',
    startangle = 90,
    wedgeprops = dict(edgecolor='white', linewidth=2)
)
for autotext in autotexts:
    autotext.set_fontsize(11)
    autotext.set_fontweight('bold')
    autotext.set_color('white')

ax_pie.set_title('Sales Share by Holiday',
                 fontsize=14, fontweight='bold', pad=10)
ax_pie.set_xticks([])
ax_pie.set_yticks([])
for spine in ax_pie.spines.values():
    spine.set_visible(False)

ax_pie.legend(
    handles=[
        mpatches.Patch(color=COLOR_NONHOLIDAY, label='Non-Holiday'),
        mpatches.Patch(color=COLOR_HOLIDAY,    label='Holiday')
    ],
    loc='lower center',
    bbox_to_anchor=(0.5, -0.12),
    ncol=2,
    fontsize=16
)

# -------------------------------------------------------
# Panel 2 — KPI card: Grand Total
# -------------------------------------------------------
ax_kpi.axis('off')
ax_kpi.add_patch(mpatches.FancyBboxPatch(
    (0.05, 0.1), 0.9, 0.8,
    boxstyle  = 'round,pad=0.05',
    linewidth = 1.5,
    edgecolor = 'lightgrey',
    facecolor = '#F8F8F8',
    transform = ax_kpi.transAxes,
    zorder    = 1
))
ax_kpi.text(
    0.5, 0.65,
    f'${grand_total/1e9:.2f}bn',
    ha='center', va='center',
    fontsize=26, fontweight='bold', color='black',
    transform=ax_kpi.transAxes, zorder=2
)
ax_kpi.text(
    0.5, 0.35,
    'Total Weekly Sales',
    ha='center', va='center',
    fontsize=16, color='grey',
    transform=ax_kpi.transAxes, zorder=2
)

# -------------------------------------------------------
# Panel 3 — KPI card: Holiday premium
# -------------------------------------------------------
ax_avg.axis('off')
ax_avg.add_patch(mpatches.FancyBboxPatch(
    (0.05, 0.1), 0.9, 0.8,
    boxstyle  = 'round,pad=0.05',
    linewidth = 1.5,
    edgecolor = 'lightgrey',
    facecolor = '#F8F8F8',
    transform = ax_avg.transAxes,
    zorder    = 1
))
ax_avg.text(
    0.5, 0.68,
    f'+{pct_diff:.1f}% on Holidays',
    ha='center', va='center',
    fontsize=16, fontweight='bold', color='darkgreen',
    transform=ax_avg.transAxes, zorder=2
)
ax_avg.text(
    0.5, 0.45,
    f'Non-Holiday: ${nonholiday_avg:,.0f}',
    ha='center', va='center',
    fontsize=11, color='grey',
    transform=ax_avg.transAxes, zorder=2
)
ax_avg.text(
    0.5, 0.28,
    f'Holiday: ${holiday_avg:,.0f}',
    ha='center', va='center',
    fontsize=11, color='grey',
    transform=ax_avg.transAxes, zorder=2
)
ax_avg.text(
    0.5, 0.12,
    'Avg Weekly Sales Comparison',
    ha='center', va='center',
    fontsize=11, color='lightgrey',
    transform=ax_avg.transAxes, zorder=2
)

# -------------------------------------------------------
# Panel 4 — Grouped bar chart: Total Sales by Store
# -------------------------------------------------------
df_false = df[df['ISHOLIDAY'] == 'FALSE'].sort_values('STORE_ID')
df_true  = df[df['ISHOLIDAY'] == 'TRUE'].sort_values('STORE_ID')

stores       = sorted(df['STORE_ID'].unique())
x            = np.arange(len(stores))
width        = 0.35

total_false  = [float(df_false[df_false['STORE_ID'] == s]['TOTAL_SALES_M'].values[0])
                if s in df_false['STORE_ID'].values else 0 for s in stores]
total_true   = [float(df_true[df_true['STORE_ID'] == s]['TOTAL_SALES_M'].values[0])
                if s in df_true['STORE_ID'].values else 0 for s in stores]

bars_false = ax_bar.bar(x - width/2, total_false, width,
                        label='Non-Holiday',
                        color=COLOR_NONHOLIDAY,
                        edgecolor='white')
bars_true  = ax_bar.bar(x + width/2, total_true, width,
                        label='Holiday',
                        color=COLOR_HOLIDAY,
                        edgecolor='white')

# Value labels on top bars only for top 10 stores by total
top10_idx = sorted(
    range(len(stores)),
    key=lambda i: total_false[i] + total_true[i],
    reverse=True
)[:10]

for i in top10_idx:
    ax_bar.text(
        x[i] - width/2, total_false[i] + 0.5,
        f'{total_false[i]:.0f}M',
        ha='center', va='bottom',
        fontsize=6.5, color=COLOR_NONHOLIDAY
    )
    ax_bar.text(
        x[i] + width/2, total_true[i] + 0.5,
        f'{total_true[i]:.0f}M',
        ha='center', va='bottom',
        fontsize=6.5, color=COLOR_HOLIDAY
    )

ax_bar.set_title('Weekly Sales by Store — Non-Holiday vs Holiday',
                 fontsize=13, fontweight='bold')
ax_bar.set_xlabel('Store ID', fontsize=11)
ax_bar.set_ylabel('Total Sales ($M)', fontsize=11)
ax_bar.set_xticks(x)
ax_bar.set_xticklabels([str(s) for s in stores], fontsize=8)
ax_bar.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: f'${v:.0f}M')
)
ax_bar.legend(fontsize=10)
ax_bar.set_facecolor('white')

# -------------------------------------------------------
# Save and show
# -------------------------------------------------------
import warnings
warnings.filterwarnings('ignore', message='This figure includes Axes')

os.makedirs('charts', exist_ok=True)
plt.subplots_adjust(
    left=0.05, right=0.95,
    top=0.95,  bottom=0.05,
    hspace=0.4, wspace=0.3
)
plt.savefig('charts/walmart_holiday_impact.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print(f"✅ Chart saved to charts/walmart_holiday_impact.png")
print(f"   Grand Total:     ${grand_total/1e9:.2f}bn")
print(f"   Holiday premium: +{pct_diff:.1f}%")
print(f"   Non-Holiday avg: ${nonholiday_avg:,.0f}")
print(f"   Holiday avg:     ${holiday_avg:,.0f}")
# %%
