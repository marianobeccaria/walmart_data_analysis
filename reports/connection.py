# connection.py
import snowflake.connector
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    return snowflake.connector.connect(
        user      = os.getenv('SNOWFLAKE_USER'),
        password  = os.getenv('SNOWFLAKE_PASSWORD'),
        account   = os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse = os.getenv('SNOWFLAKE_WAREHOUSE'),
        database  = os.getenv('SNOWFLAKE_DATABASE'),
        schema    = os.getenv('SNOWFLAKE_SCHEMA'),
        role      = os.getenv('SNOWFLAKE_ROLE')
    )

def get_dataframe(query):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    df = pd.DataFrame(
        cursor.fetchall(),
        columns=[desc[0] for desc in cursor.description]
    )
    cursor.close()
    conn.close()
    return df