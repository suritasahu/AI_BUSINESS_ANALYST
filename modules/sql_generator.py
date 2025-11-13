# modules/sql_generator.py

import os
import re
from typing import Dict
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------------------------------------------------
# Load default Gemini API key (fallback mode)
# ---------------------------------------------------------
load_dotenv()
DEFAULT_GEMINI_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = "models/gemini-2.5-flash"


# ---------------------------------------------------------
# Format schema text for Gemini
# ---------------------------------------------------------
def format_schema(schema: Dict[str, str]) -> str:
    return "\n".join([f"- {col}: {dtype}" for col, dtype in schema.items()])


# ---------------------------------------------------------
# Validate SQL doesn't use unknown columns
# ---------------------------------------------------------
def validate_sql(sql: str, schema: Dict[str, str]) -> bool:
    schema_cols = [c.lower() for c in schema.keys()]
    detected = re.findall(r"data\.([a-zA-Z_]+)", sql.lower())

    for col in detected:
        if col not in schema_cols:
            return False
    return True


# ---------------------------------------------------------
# Build prompt for Gemini
# ---------------------------------------------------------
def build_prompt(user_prompt: str, schema_text: str) -> str:
    return f"""
You are an expert SQL generator.

### RULES
- Table name is ALWAYS `data`.
- Only return SQL (NO explanations).
- Use ONLY column names listed in the schema.
- Do NOT use INSERT/UPDATE/DELETE/ALTER.
- Use GROUP BY when needed.
- Use LIMIT 100 unless user specifically requests "all".
- SQL must be valid SQLite SQL.

### SCHEMA
{schema_text}

### USER REQUEST
{user_prompt}

### OUTPUT
Return ONLY the SQL query.
"""


# ---------------------------------------------------------
# Generate SQL using Gemini
# Accepts user_api_key (preferred)
# ---------------------------------------------------------
def generate_sql_from_prompt(
    user_prompt: str,
    schema: Dict[str, str],
    api_key: str = None
) -> str:

    # ---------------------------------------
    # Configure Gemini using priority:
    # 1. User-entered key (UI)
    # 2. Fallback to .env key
    # ---------------------------------------
    active_key = api_key if api_key else DEFAULT_GEMINI_KEY

    if not active_key:
        return "SELECT * FROM data LIMIT 100;"  # no key available

    genai.configure(api_key=active_key, transport="rest")

    # ---------------------------------------
    # Prepare prompt
    # ---------------------------------------
    schema_text = format_schema(schema)
    full_prompt = build_prompt(user_prompt, schema_text)

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(full_prompt)
        sql = response.text.strip()
    except Exception as e:
        return "SELECT * FROM data LIMIT 100;"

    # ---------------------------------------
    # Cleanup SQL output
    # ---------------------------------------
    sql = re.sub(r"```sql|```", "", sql, flags=re.IGNORECASE).strip()

    if not sql.endswith(";"):
        sql += ";"

    if not sql.lower().startswith("select"):
        return "SELECT * FROM data LIMIT 100;"

    # ---------------------------------------
    # Validate columns
    # ---------------------------------------
    if validate_sql(sql, schema):
        return sql

    return "SELECT * FROM data LIMIT 100;"
