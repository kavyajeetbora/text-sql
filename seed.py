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