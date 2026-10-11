import sqlite3, sys, boto3
from dotenv import load_dotenv
import os
import sys
from gaurd import extract_sql, validate_sql

load_dotenv()

## AWS GENAI Client
REGION = "ap-south-1"                 # change to yours
MODEL_ID = os.getenv("MODEL_ID")
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

def get_schema():
    con = sqlite3.connect("shop.db")
    schema = con.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchone()[0]
    return schema

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
    print(response)
    sql_query = extract_sql(response)
    validated_sql_query = validate_sql(sql=sql_query, allowed_tables=tables)
    print("Generated and Validated SQL:",validated_sql_query)

    try: 
        result = run_sql(validated_sql_query)
        print(f"Results:\n{result}")
    except Exception as e:
        print(f"Error: {e}")

   
    
    