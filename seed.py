import sqlite3, random
from datetime import date, timedelta

random.seed(42)
con = sqlite3.connect("shop.db")
con.executescript("""
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT,
    city TEXT,
    signup_date TEXT
);
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    unit_price REAL
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER,
    order_date TEXT,
    status TEXT
);
""")

first = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Anita", "Karan", "Neha"]
last = ["Sharma", "Verma", "Singh", "Gupta", "Mehta", "Rao"]
cities = ["Delhi", "Mumbai", "Gurgaon", "Bengaluru", "Pune"]

customers = [
    (i, f"{random.choice(first)} {random.choice(last)}", random.choice(cities),
     (date(2024, 1, 1) + timedelta(days=random.randint(0, 400))).isoformat())
    for i in range(1, 51)
]
products = [
    (1, "Laptop", "Electronics", 55000), (2, "Phone", "Electronics", 20000),
    (3, "Desk", "Furniture", 8000),      (4, "Chair", "Furniture", 4500),
    (5, "Notebook", "Stationery", 120),  (6, "Pen", "Stationery", 20),
]
statuses = ["completed", "completed", "completed", "cancelled", "returned"]

# only customers 1-40 order, so customers 41-50 never ordered
orders = [
    (i, random.randint(1, 40), random.randint(1, 6), random.randint(1, 5),
     (date(2025, 1, 1) + timedelta(days=random.randint(0, 600))).isoformat(),
     random.choice(statuses))
    for i in range(1, 501)
]

con.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)
con.executemany("INSERT INTO products VALUES (?,?,?,?)", products)
con.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", orders)
con.commit()
print("done")