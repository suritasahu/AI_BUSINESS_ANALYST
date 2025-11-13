# app.py
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
import matplotlib.pyplot as plt

from modules.sql_generator import generate_sql_from_prompt
from modules.sql_executor import run_query_on_dataframe
from modules.analyzer import summarize_results

# ---------------------------------------------------------
# Streamlit Page Setup
# ---------------------------------------------------------
st.set_page_config(page_title="AI Business Analyst", layout="wide")
st.title("🤖 AI Business Analyst Dashboard")

load_dotenv()

DATA_DIR = Path("uploaded_data")
DATA_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------
# 🔐 API KEY INPUT (USER-DEFINED GEMINI KEY)
# ---------------------------------------------------------
st.sidebar.markdown("### 🔐 Enter Your Gemini API Key")

user_api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    placeholder="Enter your Gemini API key here...",
)

if user_api_key:
    st.session_state["GEMINI_API_KEY"] = user_api_key
    st.sidebar.success("API key saved!")
else:
    st.sidebar.info("Enter a Gemini API key to enable AI queries.")


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def save_uploaded_file(file, path: Path):
    with open(path, "wb") as f:
        f.write(file.getbuffer())
    return path


def safe_read_file(path: Path) -> pd.DataFrame:
    """
    Load CSV, Excel, or SQLite DB files safely.
    """
    try:
        suffix = path.suffix.lower()

        if suffix == ".csv":
            return pd.read_csv(path)

        if suffix in [".xlsx", ".xls"]:
            return pd.read_excel(path)

        if suffix == ".db":
            conn = sqlite3.connect(path)
            tables = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table';", conn
            )
            table_names = tables["name"].tolist()

            if not table_names:
                conn.close()
                raise ValueError("No tables found inside the DB.")

            selected_table = st.sidebar.selectbox("Select table", table_names)
            df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
            conn.close()
            return df

        raise ValueError("Unsupported file type.")

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return pd.DataFrame()


def display_schema(df: pd.DataFrame):
    schema = {col: str(df[col].dtype) for col in df.columns}
    st.json(schema)
    return schema


def auto_plot(df: pd.DataFrame, prompt: str):
    """
    Intelligent auto visualization:
    - For time/trend queries: line chart
    - For categorical queries: bar chart
    """
    if df.empty:
        st.warning("No data to visualize.")
        return

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        st.info("Plot skipped — no numeric columns.")
        return

    # Determine X-axis automatically
    non_numeric_cols = df.select_dtypes(exclude="number").columns.tolist()
    if non_numeric_cols:
        x_col = non_numeric_cols[0]
    else:
        df = df.reset_index()
        x_col = df.columns[0]

    y_col = numeric_cols[0]

    fig, ax = plt.subplots(figsize=(9, 4))

    if "month" in prompt.lower() or "trend" in prompt.lower() or "time" in prompt.lower():
        df.plot(x=x_col, y=y_col, marker="o", ax=ax)
    else:
        df.plot(kind="bar", x=x_col, y=y_col, ax=ax)

    ax.set_title(f"{y_col} by {x_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)

    st.pyplot(fig)


# ---------------------------------------------------------
# Sidebar — Upload or Sample Dataset
# ---------------------------------------------------------
st.sidebar.markdown("### 📂 Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV / Excel / SQLite (.db)",
    type=["csv", "xlsx", "xls", "db"]
)

if st.sidebar.button("Use sample dataset"):
    sample = pd.DataFrame({
        "order_date": pd.date_range(start="2024-01-01", periods=12, freq="M"),
        "product_name": ["Laptop", "Mobile", "Tablet", "Headphones", "Smartwatch",
                         "Laptop", "Mobile", "Tablet", "Laptop", "Smartwatch", "Headphones", "Mobile"],
        "customer_id": [1001, 1002, 1003, 1004, 1005,
                        1001, 1006, 1007, 1008, 1002, 1009, 1010],
        "amount": [1200, 899, 450, 75, 220,
                   1350, 780, 510, 1600, 260, 120, 950]
    })
    st.session_state["df"] = sample
    st.success("Sample dataset loaded!")


if uploaded_file:
    save_path = save_uploaded_file(uploaded_file, DATA_DIR / uploaded_file.name)
    df_loaded = safe_read_file(save_path)

    if not df_loaded.empty:
        st.session_state["df"] = df_loaded
        st.success(f"Loaded {uploaded_file.name} | {len(df_loaded)} rows")


# ---------------------------------------------------------
# Data Preview & Schema
# ---------------------------------------------------------
if "df" in st.session_state:
    df = st.session_state["df"]

    st.markdown("## 📊 Data Preview")
    st.dataframe(df.head(50))

    st.markdown("## 🔎 Schema")
    schema = display_schema(df)

    # Numeric summary box
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        choice = st.selectbox("Numeric column summary", ["--select--"] + numeric_cols)
        if choice != "--select--":
            st.write(df[choice].describe().to_frame().T)

else:
    st.info("Upload or load a dataset first.")
    st.stop()


# ---------------------------------------------------------
# AI Query Mode
# ---------------------------------------------------------
st.markdown("---")
st.markdown("## 💬 AI Query Mode (Natural Language → SQL → Results)")

query = st.text_input(
    "Ask a question (e.g., 'Show total amount by product_name for last 3 months')"
)

if st.button("🚀 Run AI Query"):

    if not query:
        st.warning("Please type a question.")
        st.stop()

    if "GEMINI_API_KEY" not in st.session_state:
        st.error("Enter your Gemini API Key in the sidebar first.")
        st.stop()

    api_key = st.session_state["GEMINI_API_KEY"]

    with st.spinner("Generating SQL using Gemini..."):
        sql_query = generate_sql_from_prompt(query, schema, api_key=api_key)

    st.markdown("### 🔎 Generated SQL")
    st.code(sql_query, language="sql")

    with st.spinner("Running SQL query..."):
        result_df = run_query_on_dataframe(df.copy(), sql_query)

    # Error check
    if "Error" in result_df.columns:
        st.error(result_df["Error"][0])
        st.code(result_df.get("Query", [""])[0], language="sql")
        st.stop()

    # Show results
    st.success(f"Query executed successfully — {len(result_df)} rows returned.")
    st.dataframe(result_df)

    # Summary
    st.markdown("### 📝 Summary")
    st.write(summarize_results(result_df, query))

    # Auto Plot
    st.markdown("### 📈 Visualization")
    auto_plot(result_df, query)


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("🚀 Powered by Gemini | Built with ❤️ — AI Business Analyst")
