# walmart_holiday_impact.py
# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
from plotnine import (
    ggplot, aes, geom_bar, geom_text, scale_fill_manual,
    scale_y_continuous, scale_x_discrete, labs, theme,
    theme_minimal, theme_void, element_text, element_blank,
    element_rect, position_dodge, coord_flip 
)
from mizani.formatters import label_dollar, label_comma
import os
from connection import get_dataframe

# -------------------------------------------------------
# Data
# -------------------------------------------------------
df = get_dataframe("""
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
numeric_cols = ['TOTAL_SALES', 'AVG_WEEKLY_SALES', 'WEEKS_OF_DATA']
df[numeric_cols]    = df[numeric_cols].astype(float)
df['STORE_ID']      = df['STORE_ID'].astype(str)
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
# Pie data
# -------------------------------------------------------
pie_data = pd.DataFrame({
    'ISHOLIDAY': ['FALSE', 'TRUE'],
    'TOTAL':     [nonholiday_total, holiday_total],
    'PCT':       [
        nonholiday_total / grand_total * 100,
        holiday_total    / grand_total * 100
    ]
})
pie_data         = pie_data.sort_values('ISHOLIDAY', ascending=False)
pie_data['CUMSUM']   = pie_data['PCT'].cumsum()
pie_data['MIDPOINT'] = pie_data['CUMSUM'] - pie_data['PCT'] / 2
pie_data['LABEL']    = pie_data['PCT'].apply(lambda x: f'{x:.1f}%')

# -------------------------------------------------------
# Color scheme
# -------------------------------------------------------
holiday_colors = {'FALSE': '#1F77B4', 'TRUE': '#555555'}

# -------------------------------------------------------
# Store order for x axis
# -------------------------------------------------------
store_order = [str(s) for s in sorted(df['STORE_ID'].astype(int).unique())]

# -------------------------------------------------------
# Top 10 stores for value labels
# -------------------------------------------------------
top_stores = (
    df.groupby('STORE_ID')['TOTAL_SALES']
    .sum()
    .nlargest(10)
    .index
    .tolist()
)
df['LABEL_VAL'] = df.apply(
    lambda r: f"{r['TOTAL_SALES_M']:.0f}M" if r['STORE_ID'] in top_stores else '',
    axis=1
)

# -------------------------------------------------------
# Avg comparison data
# -------------------------------------------------------
df_avg = pd.DataFrame({
    'TYPE':  ['Non-Holiday', 'Holiday'],
    'AVG':   [nonholiday_avg, holiday_avg],
    'COLOR': ['FALSE', 'TRUE'],
    'LABEL': [f'${nonholiday_avg:,.0f}', f'${holiday_avg:,.0f}']
})

# -------------------------------------------------------
# Plot 1: Grouped bar — Total Sales by Store + Holiday
# -------------------------------------------------------
p1 = (
    ggplot(df, aes(x='STORE_ID', y='TOTAL_SALES_M', fill='ISHOLIDAY'))
    + geom_bar(
        stat='identity',
        position=position_dodge(width=0.9),
        width=0.8
    )
    + geom_text(
        aes(label='LABEL_VAL'),
        position=position_dodge(width=0.9),
        va='bottom',
        size=6,
        format_string='{}'
    )
    + scale_fill_manual(
        values=holiday_colors,
        labels=['Non-Holiday', 'Holiday'],
        name='Is Holiday'
    )
    + scale_y_continuous(
        labels=lambda l: [f'${x:.0f}M' for x in l]
    )
    + scale_x_discrete(limits=store_order)
    + labs(
        title='Weekly Sales by Store — Non-Holiday vs Holiday',
        x='Store ID',
        y='Total Sales ($M)'
    )
    + theme_minimal()
    + theme(
        plot_title   = element_text(size=13, face='bold', ha='center'),
        axis_text_x  = element_text(size=7, angle=45),
        axis_text_y  = element_text(size=8),
        legend_position = 'top',
        legend_title = element_text(size=9),
        legend_text  = element_text(size=9),
        panel_grid_minor   = element_blank(),
        panel_background   = element_rect(fill='white'),
        plot_background    = element_rect(fill='white')
    )
)

# -------------------------------------------------------
# Plot 2: Pie chart — Holiday share
# -------------------------------------------------------
# p2 = (
#     ggplot(pie_data, aes(x=1, y='PCT', fill='ISHOLIDAY'))
#     + geom_bar(stat='identity', width=1, color='white', size=1)
#     + geom_text(
#         aes(y='MIDPOINT', label='LABEL'),
#         x=1,
#         size=9,
#         fontweight='bold',
#         color='white'
#     )
#     + scale_fill_manual(
#         values=holiday_colors,
#         labels=['Non-Holiday', 'Holiday'],
#         name=''
#     )
#     + coord_flip()
#     + labs(title='Sales Share\nby Holiday')
#     + theme_void()
#     + theme(
#         plot_title       = element_text(size=10, face='bold', ha='center'),
#         legend_position  = 'bottom',
#         legend_title     = element_blank(),
#         legend_text      = element_text(size=8),
#         plot_background  = element_rect(fill='white')
#     )
# )

# --- Pie chart (matplotlib directly on ax_pie) ---
ax_pie.set_facecolor('white')

pie_values  = [nonholiday_total, holiday_total]
pie_labels  = ['Non-Holiday', 'Holiday']
pie_colors  = ['#1F77B4', '#555555']
pie_explode = (0.03, 0.03)

wedges, texts, autotexts = ax_pie.pie(
    pie_values,
    labels      = None,
    colors      = pie_colors,
    explode     = pie_explode,
    autopct     = '%1.1f%%',
    startangle  = 90,
    wedgeprops  = dict(edgecolor='white', linewidth=2)
)

for autotext in autotexts:
    autotext.set_fontsize(9)
    autotext.set_fontweight('bold')
    autotext.set_color('white')

ax_pie.set_title('Sales Share\nby Holiday',
                 fontsize=10, fontweight='bold')
ax_pie.legend(
    handles=[
        mpatches.Patch(color='#1F77B4', label='Non-Holiday'),
        mpatches.Patch(color='#555555', label='Holiday')
    ],
    loc='lower center',
    bbox_to_anchor=(0.5, -0.12),
    ncol=2,
    fontsize=8
)

# -------------------------------------------------------
# Plot 3: Avg weekly sales comparison
# -------------------------------------------------------
p3 = (
    ggplot(df_avg, aes(x='TYPE', y='AVG', fill='COLOR'))
    + geom_bar(stat='identity', width=0.5)
    + geom_text(
        aes(label='LABEL'),
        va='bottom',
        size=8,
        fontweight='bold',
        format_string='{}'
    )
    + scale_fill_manual(values=holiday_colors, guide=None)
    + scale_y_continuous(
        labels=lambda l: [f'${x:,.0f}' for x in l]
    )
    + labs(
        title=f'Avg Weekly Sales\n(+{pct_diff:.1f}% on Holidays)',
        x='',
        y='Avg Weekly Sales ($)'
    )
    + theme_minimal()
    + theme(
        plot_title         = element_text(size=10, face='bold',
                                          ha='center', color='darkgreen'),
        axis_text_x        = element_text(size=9),
        axis_text_y        = element_text(size=8),
        legend_position    = 'none',
        panel_grid_minor   = element_blank(),
        panel_background   = element_rect(fill='white'),
        plot_background    = element_rect(fill='white')
    )
)

# -------------------------------------------------------
# Helper: render plotnine plot to numpy array
# -------------------------------------------------------
def plotnine_to_array(p, width_in, height_in, dpi=150):
    p_fig = p.draw()
    p_fig.set_size_inches(width_in, height_in)
    p_fig.canvas.draw()
    buf = p_fig.canvas.buffer_rgba()
    w, h = p_fig.canvas.get_width_height()
    arr = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 4)  # ← 4 channels first
    arr = arr[:, :, :3]                                          # ← then drop alpha

    plt.close(p_fig)
    return arr

# -------------------------------------------------------
# Main figure — gridspec layout
# -------------------------------------------------------
fig = plt.figure(figsize=(22, 12))
fig.patch.set_facecolor('white')
fig.suptitle('Weekly Sales by Store and Holiday',
             fontsize=20, fontweight='bold', y=1.01)

gs = gridspec.GridSpec(
    3, 2,
    width_ratios  = [1, 3],
    height_ratios = [1, 1, 1],
    hspace=0.5,
    wspace=0.3
)

ax_pie = fig.add_subplot(gs[0, 0])
ax_kpi = fig.add_subplot(gs[1, 0])
ax_avg = fig.add_subplot(gs[2, 0])
ax_bar = fig.add_subplot(gs[:, 1])

# --- Pie chart ---
ax_pie.set_axis_off()
#ax_pie.imshow(plotnine_to_array(p2, 4, 3), aspect='auto')
ax_bar.imshow(plotnine_to_array(p1, 14, 8), aspect='auto')

# --- Avg weekly bar ---
ax_avg.set_axis_off()
ax_avg.imshow(plotnine_to_array(p3, 4, 3), aspect='auto')

# --- KPI card ---
ax_kpi.axis('off')
ax_kpi.add_patch(mpatches.FancyBboxPatch(
    (0.05, 0.1), 0.9, 0.8,
    boxstyle    = 'round,pad=0.05',
    linewidth   = 1.5,
    edgecolor   = 'lightgrey',
    facecolor   = '#F8F8F8',
    transform   = ax_kpi.transAxes,
    zorder=1
))
ax_kpi.text(
    0.5, 0.65,
    f'${grand_total/1e9:.2f}bn',
    ha='center', va='center',
    fontsize=26, fontweight='bold', color='black',
    transform=ax_kpi.transAxes, zorder=2
)
ax_kpi.text(
    0.5, 0.38,
    'Total Weekly Sales',
    ha='center', va='center',
    fontsize=11, color='grey',
    transform=ax_kpi.transAxes, zorder=2
)

# --- Main grouped bar chart ---
ax_bar.set_axis_off()
ax_bar.imshow(plotnine_to_array(p1, 14, 8), aspect='auto')

# -------------------------------------------------------
# Save and show
# -------------------------------------------------------
os.makedirs('charts', exist_ok=True)
plt.tight_layout()
plt.savefig('charts/walmart_holiday_impact.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print(f"✅ Chart saved to charts/walmart_holiday_impact.png")
print(f"   Grand Total:     ${grand_total/1e9:.2f}bn")
print(f"   Holiday premium: +{pct_diff:.1f}%")
print(f"   Non-Holiday avg: ${nonholiday_avg:,.0f}")
print(f"   Holiday avg:     ${holiday_avg:,.0f}")
# %%
