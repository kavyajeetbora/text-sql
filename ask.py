import sqlite3, sys, boto3
from dotenv import load_dotenv
import os
import sys
from gaurd import extract_sql, validate_sql

load_dotenv()

GLOSSARY = """
Business rules:
- Revenue = orders.quantity * products.unit_price (join orders to products).
- Only orders with status = 'completed' count towards revenue.
- "Last month", "recent", "last N days" are relative to MAX(order_date) in the orders table, NOT the current date.
- To find customers with no orders, use a LEFT JOIN from customers to orders and check for NULL.
"""

## AWS GENAI Client
REGION = "ap-south-1"                 # change to yours
MODEL_ID = os.getenv("MODEL_ID")
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

def get_schema(rows_per_table = 3):
    con = sqlite3.connect("shop.db")

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

def query_ai(question, schema): 
    system = (
        f"""
        You are an SQLite Expert.
        Given the table schema, write one SQL Query that answers the question. 
        Return Only SQL command in SQLite Syntax, no explanation no markdown. 
        No additional information. Answer when you are 100% confident in your answer.
        Schema: 
        {schema}
        """
    )
    response = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": question}]}],
        inferenceConfig={"maxTokens": 300, "temperature": 0},
    )

    response = response["output"]["message"]["content"][0]["text"].strip()

    return response

def run_sql(query):
    con = sqlite3.connect("file:shop.db?mode=ro", uri=True)   # read-only
    cur = con.execute(query)
    cols = [c[0] for c in cur.description]
    return cols, cur.fetchall()

if __name__ == "__main__":
    query = sys.argv[1]
    schema = get_schema()
    tables = get_tables()

    response = query_ai(query, schema)
    print(r"Raw SQL Statement:\n\n")
    print(response)
    print("----"*40)
    print("Cleaned SQL Statement:")
    sql_query = extract_sql(response)
    validated_sql_query = validate_sql(sql=sql_query, allowed_tables=tables)
    print("----"*40)
    print(r"\b")
    print("Generated and Validated SQL:",validated_sql_query)
    print("**"*40)
    try: 
        result = run_sql(validated_sql_query)
        print(f"Results:\n{result}")
    except Exception as e:
        print(f"Error: {e}")

   
    
    