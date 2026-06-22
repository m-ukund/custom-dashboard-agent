-- E-commerce / SaaS schema for the Custom Dashboard Agent.
--
-- Designed to support every example request in the assignment:
--   * "Show weekly revenue by region"        -> orders + regions, time bucketed
--   * "Top customers by order volume"         -> orders grouped by customer
--   * "Monthly active users"                  -> events, distinct users per month
--   * "Break this down by product category"   -> order_items + products.category
--
-- This file is applied automatically on first container start (see
-- docker-compose.yml mounting /docker-entrypoint-initdb.d). seed.py fills the
-- tables with generated data afterwards.

CREATE TABLE IF NOT EXISTS regions (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS customers (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    region_id   INTEGER NOT NULL REFERENCES regions(id),
    signup_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    unit_price  NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)
);

-- Each order belongs to a customer. revenue lives on the line items so we can
-- break revenue down by product category as well as by region/time.
CREATE TABLE IF NOT EXISTS orders (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date  DATE NOT NULL,
    status      TEXT NOT NULL DEFAULT 'completed'
                CHECK (status IN ('completed', 'refunded', 'pending'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER NOT NULL REFERENCES orders(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)
);

-- Product/usage events, used for things like monthly active users.
CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    event_type  TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_customer    ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date        ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_order  ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_customers_region   ON customers(region_id);
CREATE INDEX IF NOT EXISTS idx_events_customer    ON events(customer_id);
CREATE INDEX IF NOT EXISTS idx_events_created     ON events(created_at);
