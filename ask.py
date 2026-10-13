import sqlite3, sys, boto3
from dotenv import load_dotenv
import os
import sys
from gaurd import extract_sql, validate_sql
from embed import retreive_tables, add_fk_neighbours
from src.logger.logs import setup_csv_logger

load_dotenv()

GLOSSARY = """
Business rules:
- Revenue = orders.quantity * products.unit_price (join orders to products).
- Only orders with status = 'completed' count towards revenue.
- "Last month", "recent", "last N days" are relative to MAX(order_date) in the orders table, NOT the current date.
- To find customers with no orders, use a LEFT JOIN from customers to orders and check for NULL.
"""

csv_log_path = r"logs/app_logs.csv"
logger = setup_csv_logger("MyCSVLogger", csv_log_path)

## AWS GENAI Client
REGION = "ap-south-1"                 # change to yours
MODEL_ID = os.getenv("MODEL_ID")
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

def get_schema(tables=None, rows_per_table = 3):
    con = sqlite3.connect("shop.db")

    if tables is None:
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]

    parts = []
    for t in tables:
        ddl = con.execute("SELECT sql FROM sqlite_master WHERE name=?", (t,)).fetchone()[0]
        cur = con.execute(f"SELECT * FROM {t} LIMIT {rows_per_table}")
        cols = [c[0] for c in cur.description]
        sample = "\n".join(" | ".join(map(str, r)) for r in cur.fetchall())
        parts.append(f"{ddl}\n/* sample rows:\n{' | '.join(cols)}\n{sample}\n*/")

    return "\n\n".join(parts)

def get_tables():
    con = sqlite3.connect('shop.db')
    rows = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tables = {r[0] for r in rows}
    return tables

def query_ai(question, schema, history=None):
    system = f"""
    You are an SQLite Expert.
    Given the table schema, write one SQL Query that answers the question.
    Return Only SQL command in SQLite Syntax, no explanation no markdown.
    Schema:
    {schema}

    {GLOSSARY}
    """
    messages = [{"role": "user", "content": [{"text": question}]}]
    if history:
        messages += history

    response = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": system}],
        messages=messages,
        inferenceConfig={"maxTokens": 300, "temperature": 0},
    )
    return response["output"]["message"]["content"][0]["text"].strip()

def run_sql(query):
    con = sqlite3.connect("file:shop.db?mode=ro", uri=True)   # read-only
    cur = con.execute(query)
    cols = [c[0] for c in cur.description]
    return cols, cur.fetchall()

MAX_RETRIES = 2

def generate_sql(question: str):
    tables = add_fk_neighbours(retreive_tables(question=question, k=4))
    schema = get_schema(tables=tables)
    allowed = get_tables()
    history, last_error = [], ""

    for attempt in range(1, MAX_RETRIES + 2):          # 1 try + 2 retries
        raw = query_ai(question, schema, history)
        try:
            sql = validate_sql(sql=extract_sql(raw), allowed_tables=allowed)
            cols, rows = run_sql(sql)
            logger.info("success", extra={"question": question, "attempt": attempt,
                                          "sql": sql, "error": ""})
            return {"sql": sql, "columns": cols, "rows": rows, "attempts": attempt}

        except (ValueError, sqlite3.Error) as e:        # fixable: feed it back
            last_error = str(e)
            logger.error("failed", extra={"question": question, "attempt": attempt,
                                          "sql": raw, "error": last_error})
            history += [
                {"role": "assistant", "content": [{"text": raw}]},
                {"role": "user", "content": [{"text": (
                    f"That query failed with this error: {last_error}\n"
                    "Fix it using only the tables and columns in the schema. "
                    "Return only the corrected SQL."
                )}]},
            ]

    return {"error": "Could not produce a working query", "last_error": last_error}


if __name__ == "__main__":
    question = sys.argv[1]
    print(generate_sql(question))

   
    
    