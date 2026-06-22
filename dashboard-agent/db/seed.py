"""Generate realistic e-commerce data for the dashboard database.

Run once after the Postgres container is up:

    python db/seed.py

The data is deliberately spread across time, regions, and product categories so
that every example request ("weekly revenue by region", "top customers by order
volume", "monthly active users", "break down by category") returns something
meaningful.

A small simulator demonstrates the assignment's "internal dashboard data may be
updating all the time" property -- it keeps inserting fresh orders/events:

    python db/seed.py --simulate

Connection settings come from DATABASE_URL (or the individual PG* defaults that
match docker-compose.yml).
"""

from __future__ import annotations

import argparse
import os
import random
import time
from datetime import date, datetime, timedelta, timezone

import psycopg

DEFAULT_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://dashboard_owner:owner_pw@localhost:5432/dashboard",
)

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]

PRODUCTS = [
    ("Starter Plan", "subscriptions", 29.00),
    ("Pro Plan", "subscriptions", 99.00),
    ("Enterprise Plan", "subscriptions", 499.00),
    ("Wireless Mouse", "electronics", 24.99),
    ("Mechanical Keyboard", "electronics", 89.99),
    ("4K Monitor", "electronics", 329.00),
    ("USB-C Hub", "accessories", 39.99),
    ("Laptop Sleeve", "accessories", 19.99),
    ("Standing Desk", "furniture", 459.00),
    ("Ergonomic Chair", "furniture", 279.00),
    ("Notebook Pack", "office_supplies", 12.50),
    ("Premium Pen Set", "office_supplies", 22.00),
]

EVENT_TYPES = ["login", "view_dashboard", "run_report", "export", "api_call"]

FIRST_NAMES = ["Ava", "Liam", "Mia", "Noah", "Zoe", "Kai", "Ivy", "Leo", "Nora", "Eli",
               "Aria", "Omar", "Sana", "Diego", "Yuki", "Lena", "Raj", "Maya", "Theo", "Isla"]
LAST_NAMES = ["Chen", "Patel", "Kim", "Garcia", "Muller", "Sato", "Silva", "Khan",
              "Nguyen", "Okafor", "Rossi", "Haddad", "Novak", "Singh", "Costa", "Park"]


def _connect() -> psycopg.Connection:
    return psycopg.connect(DEFAULT_DSN, autocommit=False)


def _is_already_seeded(conn: psycopg.Connection) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM customers")
        (count,) = cur.fetchone()
    return count > 0


def seed(num_customers: int = 200, num_orders: int = 4000, num_events: int = 12000) -> None:
    random.seed(42)
    with _connect() as conn:
        if _is_already_seeded(conn):
            print("Database already seeded; skipping. (Use --reset to wipe.)")
            return
        _insert_all(conn, num_customers, num_orders, num_events)
        conn.commit()
    print(
        f"Seeded {len(REGIONS)} regions, {len(PRODUCTS)} products, "
        f"{num_customers} customers, {num_orders} orders, {num_events} events."
    )


def reset_and_seed(**kwargs) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE order_items, orders, events, customers, products, regions "
                "RESTART IDENTITY CASCADE"
            )
        conn.commit()
    seed(**kwargs)


def _insert_all(conn: psycopg.Connection, num_customers: int, num_orders: int, num_events: int) -> None:
    today = date.today()
    start = today - timedelta(days=365)

    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO regions (name) VALUES (%s)", [(r,) for r in REGIONS]
        )
        cur.execute("SELECT id FROM regions ORDER BY id")
        region_ids = [r[0] for r in cur.fetchall()]

        cur.executemany(
            "INSERT INTO products (name, category, unit_price) VALUES (%s, %s, %s)",
            PRODUCTS,
        )
        cur.execute("SELECT id, unit_price FROM products ORDER BY id")
        products = cur.fetchall()

        customers = []
        for i in range(num_customers):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
            signup = start + timedelta(days=random.randint(0, 300))
            customers.append((f"{fn} {ln}", email, random.choice(region_ids), signup))
        cur.executemany(
            "INSERT INTO customers (name, email, region_id, signup_date) "
            "VALUES (%s, %s, %s, %s)",
            customers,
        )
        cur.execute("SELECT id, signup_date FROM customers ORDER BY id")
        customer_rows = cur.fetchall()

        orders = []
        for _ in range(num_orders):
            cust_id, signup = random.choice(customer_rows)
            earliest = max(signup, start)
            span = (today - earliest).days
            order_date = earliest + timedelta(days=random.randint(0, max(span, 0)))
            status = random.choices(
                ["completed", "refunded", "pending"], weights=[88, 7, 5]
            )[0]
            orders.append((cust_id, order_date, status))
        cur.executemany(
            "INSERT INTO orders (customer_id, order_date, status) VALUES (%s, %s, %s)",
            orders,
        )
        cur.execute("SELECT id FROM orders ORDER BY id")
        order_ids = [r[0] for r in cur.fetchall()]

        line_items = []
        for order_id in order_ids:
            for _ in range(random.randint(1, 4)):
                prod_id, unit_price = random.choice(products)
                qty = random.randint(1, 5)
                line_items.append((order_id, prod_id, qty, unit_price))
        cur.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
            "VALUES (%s, %s, %s, %s)",
            line_items,
        )

        events = []
        for _ in range(num_events):
            cust_id, _signup = random.choice(customer_rows)
            ts = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            events.append((cust_id, random.choice(EVENT_TYPES), ts))
        cur.executemany(
            "INSERT INTO events (customer_id, event_type, created_at) VALUES (%s, %s, %s)",
            events,
        )


def simulate(interval_s: float = 2.0) -> None:
    """Continuously insert fresh orders + events to mimic live data."""
    print(f"Simulating live data every {interval_s}s. Ctrl+C to stop.")
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM customers")
            customer_ids = [r[0] for r in cur.fetchall()]
            cur.execute("SELECT id, unit_price FROM products")
            products = cur.fetchall()
        if not customer_ids or not products:
            print("No seed data found. Run `python db/seed.py` first.")
            return
        try:
            while True:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO orders (customer_id, order_date, status) "
                        "VALUES (%s, %s, 'completed') RETURNING id",
                        (random.choice(customer_ids), date.today()),
                    )
                    (order_id,) = cur.fetchone()
                    for _ in range(random.randint(1, 3)):
                        prod_id, unit_price = random.choice(products)
                        cur.execute(
                            "INSERT INTO order_items "
                            "(order_id, product_id, quantity, unit_price) "
                            "VALUES (%s, %s, %s, %s)",
                            (order_id, prod_id, random.randint(1, 4), unit_price),
                        )
                    cur.execute(
                        "INSERT INTO events (customer_id, event_type, created_at) "
                        "VALUES (%s, %s, now())",
                        (random.choice(customer_ids), random.choice(EVENT_TYPES)),
                    )
                conn.commit()
                print(f"  + order {order_id} and one event")
                time.sleep(interval_s)
        except KeyboardInterrupt:
            print("\nStopped simulator.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the dashboard database")
    parser.add_argument("--reset", action="store_true", help="wipe then reseed")
    parser.add_argument("--simulate", action="store_true", help="continuously insert live data")
    parser.add_argument("--interval", type=float, default=2.0, help="simulate interval seconds")
    args = parser.parse_args()

    if args.simulate:
        simulate(args.interval)
    elif args.reset:
        reset_and_seed()
    else:
        seed()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
