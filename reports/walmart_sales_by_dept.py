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
        AVG_WEEKLY_SALES
    FROM WALMART_DB.GOLD.WALMART_SALES_BY_DEPT
    ORDER BY TOTAL_SALES DESC
    LIMIT 20
""")

# Create combined label
df['LABEL'] = 'Dept ' + df['DEPT_ID'].astype(str) + '\n(Store ' + df['STORE_ID'].astype(str) + ')'

# Assign unique color per store
unique_stores = df['STORE_ID'].unique()
color_palette = cm.tab20(np.linspace(0, 1, len(unique_stores)))
store_color_map = dict(zip(unique_stores, color_palette))
bar_colors = df['STORE_ID'].map(store_color_map)

# Legend elements — defined once, reused in both charts
legend_elements = [
    Patch(facecolor=store_color_map[s], label=f'Store {s}')
    for s in sorted(unique_stores)
]

# -------------------------------------------------------
# Chart 1: Total Sales by Dept/Store
# -------------------------------------------------------
fig, ax = plt.subplots(figsize=(18, 7))

bars = ax.bar(
    df['LABEL'],
    df['TOTAL_SALES'],
    color=bar_colors,
    edgecolor='white',
    width=0.6
)

for bar in bars:
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f'${bar.get_height()/1e6:.1f}M',
        ha='center', va='bottom', fontsize=8
    )

ax.set_title('Top 20 Department/Store Combinations by Total Sales',
             fontsize=15, fontweight='bold', pad=15)
ax.set_xlabel('Department (Store)', fontsize=12)
ax.set_ylabel('Total Sales ($)', fontsize=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x/1e6:.0f}M'))
plt.xticks(rotation=45, ha='right', fontsize=9)
ax.legend(handles=legend_elements, title='Store ID',
          bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=8)
plt.tight_layout()

os.makedirs('charts', exist_ok=True)
plt.savefig('charts/walmart_sales_by_dept_total.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# -------------------------------------------------------
# Chart 2: Avg Weekly Sales by Dept/Store
# -------------------------------------------------------
fig, ax = plt.subplots(figsize=(18, 7))

bars = ax.bar(
    df['LABEL'],                  # same top 20 as Chart 1
    df['AVG_WEEKLY_SALES'],       # ← only change from Chart 1
    color=bar_colors,
    edgecolor='white',
    width=0.6
)

for bar in bars:
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f'${bar.get_height():,.0f}',
        ha='center', va='bottom', fontsize=8
    )

ax.set_title('Top 20 Department/Store Combinations by Avg Weekly Sales',
             fontsize=15, fontweight='bold', pad=15)
ax.set_xlabel('Department (Store)', fontsize=12)
ax.set_ylabel('Avg Weekly Sales ($)', fontsize=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
plt.xticks(rotation=45, ha='right', fontsize=9)
ax.legend(handles=legend_elements, title='Store ID',
          bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=8)
plt.tight_layout()

plt.savefig('charts/walmart_sales_by_dept_avg.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# -------------------------------------------------------
# Chart 3: Both metrics side by side (grouped bar)
# -------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 7))
fig.suptitle('Top 20 Department/Store — Total vs Avg Weekly Sales',
             fontsize=15, fontweight='bold')

# Left: Total Sales
ax1.bar(df['LABEL'], df['TOTAL_SALES'], color=bar_colors, edgecolor='white', width=0.6)
ax1.set_title('Total Sales', fontsize=13)
ax1.set_xlabel('Department (Store)', fontsize=11)
ax1.set_ylabel('Total Sales ($)', fontsize=11)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x/1e6:.0f}M'))
ax1.tick_params(axis='x', rotation=45, labelsize=8)

# Right: Avg Weekly Sales
ax2.bar(df['LABEL'], df['AVG_WEEKLY_SALES'], color=bar_colors, edgecolor='white', width=0.6)
ax2.set_title('Avg Weekly Sales', fontsize=13)
ax2.set_xlabel('Department (Store)', fontsize=11)
ax2.set_ylabel('Avg Weekly Sales ($)', fontsize=11)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax2.tick_params(axis='x', rotation=45, labelsize=8)

# Shared legend at bottom
fig.legend(handles=legend_elements, title='Store ID',
           loc='lower center', ncol=10,
           bbox_to_anchor=(0.5, -0.08), fontsize=8)
plt.tight_layout()

plt.savefig('charts/walmart_sales_by_dept_combined.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print(" Charts saved to charts/")