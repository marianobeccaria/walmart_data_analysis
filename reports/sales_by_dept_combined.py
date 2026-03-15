# walmart_sales_by_dept.py
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.cm as cm
import numpy as np
import os
from matplotlib.patches import Patch
from connection import get_dataframe

# --- Data ---
df = get_dataframe("""
    SELECT
        STORE_ID,
        DEPT_ID,
        TOTAL_SALES,
        AVG_WEEKLY_SALES,
        MAX_WEEKLY_SALES,
        MIN_WEEKLY_SALES
    FROM WALMART_DB.GOLD.WALMART_SALES_BY_DEPT
    ORDER BY TOTAL_SALES DESC
    LIMIT 20
""")

# Also fetch store type for donut chart
df_store_type = get_dataframe("""
    SELECT
        s.STORE_TYPE,
        SUM(d.TOTAL_SALES)      AS TOTAL_SALES
    FROM WALMART_DB.GOLD.WALMART_SALES_BY_DEPT d
    LEFT JOIN WALMART_DB.SILVER.WALMART_STORE_DIM s
        ON d.STORE_ID = s.STORE_ID
    GROUP BY s.STORE_TYPE
    ORDER BY TOTAL_SALES DESC
""")

# Convert decimals to float
numeric_cols = ['TOTAL_SALES', 'AVG_WEEKLY_SALES', 'MAX_WEEKLY_SALES', 'MIN_WEEKLY_SALES']
df[numeric_cols]              = df[numeric_cols].astype(float)
df_store_type['TOTAL_SALES']  = df_store_type['TOTAL_SALES'].astype(float)

# Labels and colors
df['LABEL'] = 'Dept ' + df['DEPT_ID'].astype(str) + ' (Store ' + df['STORE_ID'].astype(str) + ')'
unique_stores   = df['STORE_ID'].unique()
color_palette   = cm.tab20(np.linspace(0, 1, len(unique_stores)))
store_color_map = dict(zip(unique_stores, color_palette))
bar_colors      = list(df['STORE_ID'].map(store_color_map))

legend_elements = [
    Patch(facecolor=store_color_map[s], label=f'Store {s}')
    for s in sorted(unique_stores)
]

# Grand total across ALL departments (not just top 20)
df_all = get_dataframe("""
    SELECT SUM(TOTAL_SALES) AS GRAND_TOTAL
    FROM WALMART_DB.GOLD.WALMART_SALES_BY_DEPT
""")
grand_total = float(df_all['GRAND_TOTAL'].iloc[0])

# -------------------------------------------------------
# Single figure 2x2
# -------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(28, 18))
fig.suptitle('Walmart — Top 20 Department/Store Sales Analysis',
             fontsize=20, fontweight='bold', y=1.01)

x     = np.arange(len(df))

# -------------------------------------------------------
# Chart 1 (top left): Total vs Avg Weekly Sales side by side
# -------------------------------------------------------
ax1   = axes[0, 0]
width = 0.4

bars1a = ax1.bar(x - width/2, df['TOTAL_SALES'] / 1e6, width,
                 label='Total Sales ($M)',  color='steelblue',  edgecolor='white')
bars1b = ax1.bar(x + width/2, df['AVG_WEEKLY_SALES'] / 1e3, width,
                 label='Avg Weekly ($K)',   color='darkorange', edgecolor='white')

# Value labels
for bar in bars1a:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
             f'${bar.get_height():.1f}M',
             ha='center', va='bottom', fontsize=7, color='steelblue')

for bar in bars1b:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
             f'${bar.get_height():.1f}K',
             ha='center', va='bottom', fontsize=7, color='darkorange')

# Grand total annotation with arrow pointing to tallest bar
tallest_bar_x = 0  # first bar is highest since sorted DESC
tallest_bar_y = float(df['TOTAL_SALES'].iloc[0]) / 1e6

ax1.annotate(
    f'Grand Total\nAll Depts:\n${grand_total/1e9:.2f}B',
    xy=(tallest_bar_x - width/2, tallest_bar_y),       # arrow points to
    xytext=(tallest_bar_x + 3, tallest_bar_y + 3),     # text position
    fontsize=9,
    fontweight='bold',
    color='darkred',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow',
              edgecolor='darkred', linewidth=1.5),
    arrowprops=dict(arrowstyle='->', color='darkred', lw=2)
)

ax1.set_title('Total Sales ($M) vs Avg Weekly Sales ($K)',
              fontsize=12, fontweight='bold')
ax1.set_xlabel('Department (Store)', fontsize=10)
ax1.set_ylabel('Sales', fontsize=10)
ax1.set_xticks(x)
ax1.set_xticklabels(df['LABEL'], rotation=45, ha='right', fontsize=7)
ax1.legend(fontsize=9)

# -------------------------------------------------------
# Chart 2 (top right): Min / Avg / Max grouped bars
# -------------------------------------------------------
ax2   = axes[0, 1]
width = 0.25

ax2.bar(x - width, df['MAX_WEEKLY_SALES'], width,
        label='Max Weekly', color='steelblue',  edgecolor='white')
ax2.bar(x,         df['AVG_WEEKLY_SALES'], width,
        label='Avg Weekly', color='darkorange', edgecolor='white')
ax2.bar(x + width, df['MIN_WEEKLY_SALES'], width,
        label='Min Weekly', color='tomato',     edgecolor='white')

ax2.axhline(y=0, color='black', linewidth=0.8, linestyle='-')
ax2.set_ylim(bottom=float(df['MIN_WEEKLY_SALES'].min()) * 1.2)
ax2.set_title('Min / Avg / Max Weekly Sales per Department',
              fontsize=12, fontweight='bold')
ax2.set_xlabel('Department (Store)', fontsize=10)
ax2.set_ylabel('Weekly Sales ($)', fontsize=10)
ax2.set_xticks(x)
ax2.set_xticklabels(df['LABEL'], rotation=45, ha='right', fontsize=7)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax2.legend(fontsize=9)

# -------------------------------------------------------
# Chart 3 (bottom left): Horizontal ranked bar
# -------------------------------------------------------
ax3 = axes[1, 0]

# Reverse so highest is at top
df_h        = df.iloc[::-1].reset_index(drop=True)
bar_colors_h = list(df['STORE_ID'].map(store_color_map))[::-1]

bars3 = ax3.barh(
    df_h['LABEL'],
    df_h['TOTAL_SALES'] / 1e6,
    color=bar_colors_h,
    edgecolor='white',
    height=0.6
)

# Value labels at end of each bar
for bar in bars3:
    ax3.text(
        bar.get_width() + 0.1,
        bar.get_y() + bar.get_height() / 2,
        f'${bar.get_width():.1f}M',
        ha='left', va='center', fontsize=8
    )

ax3.set_title('Top 20 Departments Ranked by Total Sales',
              fontsize=12, fontweight='bold')
ax3.set_xlabel('Total Sales ($M)', fontsize=10)
ax3.set_ylabel('Department (Store)', fontsize=10)
ax3.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.0f}M'))
ax3.tick_params(axis='y', labelsize=8)
ax3.legend(handles=legend_elements, title='Store ID',
           bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=7)

# -------------------------------------------------------
# Chart 4 (bottom right): Store Type donut chart
# -------------------------------------------------------
ax4          = axes[1, 1]
type_colors  = {'A': 'steelblue', 'B': 'darkorange', 'C': 'green'}
donut_colors = [type_colors.get(t, 'grey') for t in df_store_type['STORE_TYPE']]
total        = df_store_type['TOTAL_SALES'].sum()

wedges, texts, autotexts = ax4.pie(
    df_store_type['TOTAL_SALES'],
    labels=None,
    colors=donut_colors,
    autopct=lambda pct: f'{pct:.1f}%\n(${pct/100*total/1e9:.1f}B)',
    pctdistance=0.75,
    startangle=90,
    wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)  # donut hole
)

# Style the percentage text
for autotext in autotexts:
    autotext.set_fontsize(9)
    autotext.set_fontweight('bold')

# Centre label showing overall grand total
ax4.text(0, 0, f'Total\n${total/1e9:.1f}B',
         ha='center', va='center', fontsize=12, fontweight='bold', color='black')

ax4.set_title('Total Sales Share by Store Type', fontsize=12, fontweight='bold')
ax4.legend(
    handles=[Patch(facecolor=type_colors[t], label=f'Type {t}')
             for t in df_store_type['STORE_TYPE']],
    title='Store Type',
    loc='lower center',
    bbox_to_anchor=(0.5, -0.08),
    ncol=3,
    fontsize=10
)

# -------------------------------------------------------
# Final layout and save
# -------------------------------------------------------
plt.tight_layout()
os.makedirs('charts', exist_ok=True)
plt.savefig('charts/walmart_sales_by_dept_all.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print(f" Chart saved to charts/walmart_sales_by_dept_all.png")
print(f"   Grand Total across all departments: ${grand_total/1e9:.2f}B")