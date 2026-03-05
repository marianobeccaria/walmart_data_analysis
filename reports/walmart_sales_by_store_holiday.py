import snowflake.connector
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from dotenv import load_dotenv
import os

load_dotenv()

conn = snowflake.connector.connect(
    user      = os.getenv('SNOWFLAKE_USER'),
    password  = os.getenv('SNOWFLAKE_PASSWORD'),
    account   = os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE'),
    database  = os.getenv('SNOWFLAKE_DATABASE'),
    schema    = os.getenv('SNOWFLAKE_SCHEMA'),
    role      = os.getenv('SNOWFLAKE_ROLE')
)

cursor = conn.cursor()
cursor.execute("""
    SELECT
        STORE_ID,
        STORE_TYPE,
        STORE_SIZE,
        ISHOLIDAY,
        TOTAL_SALES,
        AVG_WEEKLY_SALES,
        WEEKS_OF_DATA
    FROM WALMART_DB.GOLD.WALMART_SALES_BY_STORE
    ORDER BY STORE_ID, ISHOLIDAY
""")

df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
cursor.close()
conn.close()

# ────────────────────────────────────────────────
# Separate holiday vs non-holiday
df_holiday     = df[df['ISHOLIDAY'] == True]
df_non_holiday = df[df['ISHOLIDAY'] == False]

# ────────────────────────────────────────────────
# Calculate totals for pie chart
total_holiday    = df_holiday['TOTAL_SALES'].sum()
total_non_holiday = df_non_holiday['TOTAL_SALES'].sum()
sizes = [total_non_holiday, total_holiday]
labels = ['Non-Holiday', 'Holiday']
colors = ['lightgray', 'coral']          # or any colors you prefer

# ────────────────────────────────────────────────
# Create figure with 3 subplots side by side
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 7))
fig.suptitle('Weekly Sales by Store — Holiday vs Non-Holiday + Overall Distribution', 
             fontsize=16, fontweight='bold')
             
# # Create figure with 2 subplots side by side
# fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))
# fig.suptitle('Weekly Sales by Store — Holiday vs Non-Holiday', fontsize=16, fontweight='bold')

# Color map for store types
color_map = {'A': 'steelblue', 'B': 'orange', 'C': 'green'}

# ────────────────────────────────────────────────
# Chart 1 — Non-Holiday sales
ax1.bar(
    df_non_holiday['STORE_ID'].astype(str),
    df_non_holiday['TOTAL_SALES'],
    color=df_non_holiday['STORE_TYPE'].map(color_map)
)
ax1.set_title('Non-Holiday Weeks', fontsize=13)
ax1.set_xlabel('Store ID')
ax1.set_ylabel('Total Sales ($)')
ax1.tick_params(axis='x', rotation=45)

# ────────────────────────────────────────────────
# Chart 2 — Holiday sales
ax2.bar(
    df_holiday['STORE_ID'].astype(str),
    df_holiday['TOTAL_SALES'],
    color=df_holiday['STORE_TYPE'].map(color_map)
)
ax2.set_title('Holiday Weeks', fontsize=13)
ax2.set_xlabel('Store ID')
ax2.set_ylabel('Total Sales ($)')
ax2.tick_params(axis='x', rotation=45)

# ────────────────────────────────────────────────
# Chart 3 — Pie chart: Holiday vs Non-Holiday share
wedges, texts, autotexts = ax3.pie(
    sizes,
    labels=labels,
    colors=colors,
    autopct='%1.1f%%',
    startangle=90,
    textprops={'fontsize': 12},
    pctdistance=0.75
)
ax3.set_title('Overall Sales Distribution', fontsize=13)

# Equal aspect ratio ensures pie is drawn as a circle
ax3.axis('equal')

# ────────────────────────────────────────────────
# Shared legend for store types
legend_elements = [
    Patch(facecolor='steelblue', label='Type A'),
    Patch(facecolor='orange',    label='Type B'),
    Patch(facecolor='green',     label='Type C')
]
fig.legend(handles=legend_elements, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.05))

plt.tight_layout()
plt.subplots_adjust(top=0.92, bottom=0.12)   # give space for legend
plt.show()
