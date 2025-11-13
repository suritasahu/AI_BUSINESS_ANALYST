# modules/sql_executor.py

import pandas as pd
import sqlite3

def run_query_on_dataframe(df: pd.DataFrame, query: str):
    try:
        conn = sqlite3.connect(":memory:")

        # Convert datetime columns to strings (SQLite-safe)
        for col in df.columns:
            if "date" in col.lower() or df[col].dtype == "datetime64[ns]":
                df[col] = df[col].astype(str)

        df.to_sql("data", conn, index=False, if_exists="replace")
        output = pd.read_sql_query(query, conn)
        conn.close()

        return output

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)], "Query": [query]})
