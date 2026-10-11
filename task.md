Here's the 30-minute version: one table, one seed script, one ask script.

## Setup (about 5 min)

```bash
uv init text2sql && cd text2sql
uv add boto3
aws configure        # access key, secret, region (e.g. ap-south-1)
```

In the Bedrock console, open **Model catalog**, pick a cheap model such as **Amazon Nova Micro**, and copy its **model ID**. In some regions, including Mumbai, you need the *inference profile ID* instead, which is the model ID with a prefix like `apac.`. Use whichever ID the console gives you.

## File 1: `seed.py` (random data)

```python
import sqlite3, random
from datetime import date, timedelta

random.seed(42)
con = sqlite3.connect("shop.db")
con.execute("DROP TABLE IF EXISTS orders")
con.execute("""
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_name TEXT,
    city TEXT,
    product TEXT,
    category TEXT,
    quantity INTEGER,
    unit_price REAL,
    order_date TEXT
)""")

names = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Anita", "Karan", "Neha"]
cities = ["Delhi", "Mumbai", "Gurgaon", "Bengaluru", "Pune"]
products = {"Laptop": ("Electronics", 55000), "Phone": ("Electronics", 20000),
            "Desk": ("Furniture", 8000), "Chair": ("Furniture", 4500),
            "Notebook": ("Stationery", 120), "Pen": ("Stationery", 20)}

rows = []
for i in range(1, 501):
    p = random.choice(list(products))
    cat, price = products[p]
    d = date(2025, 1, 1) + timedelta(days=random.randint(0, 600))
    rows.append((i, random.choice(names), random.choice(cities), p, cat,
                 random.randint(1, 5), price, d.isoformat()))

con.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", rows)
con.commit()
print("Inserted", len(rows), "rows")
```

Run it with `uv run seed.py`.

## File 2: `ask.py` (Bedrock to SQL to result)

```python
import sqlite3, sys, boto3

REGION = "ap-south-1"                 # change to yours
MODEL_ID = "PASTE_MODEL_OR_PROFILE_ID_HERE"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

def get_schema():
    con = sqlite3.connect("shop.db")
    return con.execute(
        "SELECT sql FROM sqlite_master WHERE type='table'").fetchone()[0]

def generate_sql(question, schema):
    system = (
        "You are a SQLite expert. Given the table schema, write ONE SQL query "
        "that answers the question. Return only the SQL, no explanation, no markdown.\n\n"
        f"Schema:\n{schema}"
    )
    resp = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": question}]}],
        inferenceConfig={"maxTokens": 300, "temperature": 0},
    )
    sql = resp["output"]["message"]["content"][0]["text"].strip()
    return sql.replace("```sql", "").replace("```", "").strip()

def run_sql(sql):
    con = sqlite3.connect("file:shop.db?mode=ro", uri=True)   # read-only
    cur = con.execute(sql)
    cols = [c[0] for c in cur.description]
    return cols, cur.fetchall()

if __name__ == "__main__":
    question = " ".join(sys.argv[1:])
    sql = generate_sql(question, get_schema())
    print("SQL:", sql, "\n")
    cols, rows = run_sql(sql)
    print(cols)
    for r in rows[:20]:
        print(r)
```

Try it:

```bash
uv run ask.py "What is the total revenue by city?"
uv run ask.py "Top 3 products by quantity sold"
uv run ask.py "How many orders were placed in 2025?"
```

## What to notice

- **Revenue:** there's no `total` column. The model has to work out `quantity * unit_price`, which is the first sign you need a business glossary later.
- **Read-only:** the database opens with `mode=ro`, so even a bad `DELETE` can't run. That's your minimal guardrail.
- **Reliability:** run the same question 3 times. At temperature 0 it should return the same SQL each time.
- **Failures:** try a vague question like "best customers" and see what it guesses.

## Common errors

- **`AccessDeniedException` or "model access":** the model isn't enabled for your account or region.
- **"on-demand throughput isn't supported":** you need the inference profile ID, not the plain model ID.
- **`NoCredentialsError`:** run `aws configure` again.

Paste any error or output here and we'll debug it together. When it works, tell me what happened with "best customers" and we'll decide what to build next.