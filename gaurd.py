import sqlglot
import re
from sqlglot import exp


def extract_sql(text: str) -> str:
    # 1. If the model used a ```sql ... ``` block, take what's inside it
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
    # 2. Drop any chatter before the first SELECT / WITH
    m = re.search(r"\b(select|with)\b", text, re.IGNORECASE)
    if m:
        text = text[m.start():]
    # 3. Remove trailing semicolon and whitespace
    return text.strip().rstrip(";").strip()


FORBIDDEN = (exp.Insert, exp.Update, exp.Delete, exp.Drop,
             exp.Create, exp.Alter, exp.Command)


def validate_sql(sql: str, allowed_tables: set, max_rows: int = 100) -> str:
    # Parse into a syntax tree (fails if it isn't valid SQL)
    try:
        statements = sqlglot.parse(sql, dialect="sqlite")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"SQL could not be parsed: {e}")

    statements = [s for s in statements if s is not None]

    # Check 1: exactly one statement
    if len(statements) != 1:
        raise ValueError("Exactly one SQL statement is allowed")
    tree = statements[0]

    # Check 2: must be a read query
    if not isinstance(tree, (exp.Select, exp.Union)):
        raise ValueError("Only SELECT queries are allowed")

    # Check 3: no write/DDL node hiding anywhere inside the tree
    if tree.find(*FORBIDDEN):
        raise ValueError("Write or DDL operations are not allowed")

    # Check 4: only allowed tables (CTE names like "WITH x AS ..." are fine)
    cte_names = {cte.alias for cte in tree.find_all(exp.CTE)}
    for t in tree.find_all(exp.Table):
        if t.name not in allowed_tables and t.name not in cte_names:
            raise ValueError(f"Table not allowed: {t.name}")

    # Row limit (Step 3, below)
    if tree.args.get("limit") is None:
        tree = tree.limit(max_rows)

    ## This is already in the last lines of validate_sql. 
    ## If the model forgot a LIMIT, one is added automatically, 
    ## so "show all orders" can’t dump millions of rows into your terminal or your API response.

    return tree.sql(dialect="sqlite")

