import sqlite3
from catalog import EXTRA_TABLES

con = sqlite3.connect("shop.db")

for name, cols in EXTRA_TABLES.items():
    con.execute(f"DROP TABLE IF EXISTS {name}")
    con.execute(f"CREATE TABLE {name} ({cols})")
con.commit()
print("tables now:", len(con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()))