"""Scripted model responses + canned query results, keyed by eval case name.

Each entry provides:
  * "model":  the sequence of text responses the mock model returns, in order
              (first call is triage, then plan, then any corrective retry).
  * "result": the MockResult the mock executor returns for that case (or None to
              simulate a query/table failure). Unused when triage rejects.

These deliberately cover the happy path, messy input, ambiguity/clarification,
and the three corrective-retry paths (unsafe SQL, execution error, bad spec),
plus an API-error case -- the same failure taxonomy the real system handles.
"""

from __future__ import annotations

import json

import anthropic

from evals.mock_client import MockResult

# A schema snapshot matching db/schema.sql, fed to the (mocked) model so prompts
# look realistic. The model is scripted, so exact content doesn't affect scoring.
SCHEMA_TEXT = """TABLE regions (id integer NOT NULL, name text NOT NULL)
TABLE customers (id integer NOT NULL, name text NOT NULL, email text NOT NULL, region_id integer NOT NULL, signup_date date NOT NULL)
  FK region_id -> regions.id
TABLE products (id integer NOT NULL, name text NOT NULL, category text NOT NULL, unit_price numeric NOT NULL)
TABLE orders (id integer NOT NULL, customer_id integer NOT NULL, order_date date NOT NULL, status text NOT NULL)
  FK customer_id -> customers.id
TABLE order_items (id integer NOT NULL, order_id integer NOT NULL, product_id integer NOT NULL, quantity integer NOT NULL, unit_price numeric NOT NULL)
  FK order_id -> orders.id
  FK product_id -> products.id
TABLE events (id integer NOT NULL, customer_id integer NOT NULL, event_type text NOT NULL, created_at timestamp NOT NULL)
  FK customer_id -> customers.id"""


def _triage(answerable: bool, reason: str = "", clarification: str | None = None) -> str:
    return json.dumps(
        {"answerable": answerable, "reason": reason, "clarification": clarification}
    )


def _plan(sql, title, widget_type, encoding, notes=None) -> str:
    return json.dumps(
        {"sql": sql, "title": title, "widget_type": widget_type,
         "encoding": encoding, "notes": notes}
    )


MOCK_RESPONSES: dict[str, dict] = {
    "clean_revenue_region": {
        "model": [
            _triage(True, "revenue, regions, and order dates all exist"),
            _plan(
                "SELECT date_trunc('week', o.order_date) AS week, r.name AS region, "
                "SUM(oi.quantity * oi.unit_price) AS revenue "
                "FROM orders o JOIN customers c ON c.id = o.customer_id "
                "JOIN regions r ON r.id = c.region_id "
                "JOIN order_items oi ON oi.order_id = o.id "
                "GROUP BY 1, 2 ORDER BY 1",
                "Weekly revenue by region", "line",
                {"x": "week", "y": "revenue", "series": "region",
                 "value": None, "label": None, "value_format": "currency"},
            ),
        ],
        "result": MockResult(
            columns=[("week", "timestamp"), ("region", "text"), ("revenue", "numeric")],
            rows=[
                {"week": "2026-01-05", "region": "Europe", "revenue": 1200.0},
                {"week": "2026-01-05", "region": "Asia Pacific", "revenue": 980.0},
                {"week": "2026-01-12", "region": "Europe", "revenue": 1400.0},
            ],
        ),
    },
    "top_customers": {
        "model": [
            _triage(True, "orders per customer is computable"),
            _plan(
                "SELECT c.name AS customer_name, COUNT(*) AS order_count "
                "FROM orders o JOIN customers c ON c.id = o.customer_id "
                "GROUP BY c.name ORDER BY order_count DESC LIMIT 10",
                "Top customers by order volume", "bar",
                {"x": "customer_name", "y": "order_count", "series": None,
                 "value": None, "label": None, "value_format": "number"},
            ),
        ],
        "result": MockResult(
            columns=[("customer_name", "text"), ("order_count", "int")],
            rows=[{"customer_name": "Ava Chen", "order_count": 31},
                  {"customer_name": "Leo Park", "order_count": 27}],
        ),
    },
    "mau_metric": {
        "model": [
            _triage(True, "events table supports active-user counts"),
            _plan(
                "SELECT COUNT(DISTINCT customer_id) AS active_users FROM events "
                "WHERE created_at >= date_trunc('month', now())",
                "Monthly active users", "metric",
                {"x": None, "y": None, "series": None, "value": "active_users",
                 "label": None, "value_format": "number"},
            ),
        ],
        "result": MockResult(
            columns=[("active_users", "int")], rows=[{"active_users": 142}]
        ),
    },
    "category_bar": {
        "model": [
            _triage(True, "products.category enables this breakdown"),
            _plan(
                "SELECT p.category AS category, SUM(oi.quantity * oi.unit_price) AS revenue "
                "FROM order_items oi JOIN products p ON p.id = oi.product_id "
                "GROUP BY p.category ORDER BY revenue DESC",
                "Revenue by product category", "bar",
                {"x": "category", "y": "revenue", "series": None,
                 "value": None, "label": None, "value_format": "currency"},
            ),
        ],
        "result": MockResult(
            columns=[("category", "text"), ("revenue", "numeric")],
            rows=[{"category": "subscriptions", "revenue": 50100.0},
                  {"category": "electronics", "revenue": 23400.0}],
        ),
    },
    "messy_typos": {
        # "shwo me revenu by categry pls!!" -- model still resolves intent.
        "model": [
            _triage(True, "interpreted as revenue by category"),
            _plan(
                "SELECT p.category AS category, SUM(oi.quantity * oi.unit_price) AS revenue "
                "FROM order_items oi JOIN products p ON p.id = oi.product_id "
                "GROUP BY p.category ORDER BY revenue DESC",
                "Revenue by category", "bar",
                {"x": "category", "y": "revenue", "series": None,
                 "value": None, "label": None, "value_format": "currency"},
            ),
        ],
        "result": MockResult(
            columns=[("category", "text"), ("revenue", "numeric")],
            rows=[{"category": "furniture", "revenue": 18000.0}],
        ),
    },
    "ambiguous_clarify": {
        # "make it look better" -- not answerable, ask for clarification.
        "model": [
            _triage(False, "request is not a concrete data question",
                    "What metric would you like to see, and broken down by what?"),
        ],
        "result": None,
    },
    "unknown_table": {
        # "show employee salaries" -- no such data in this schema.
        "model": [
            _triage(False, "schema has no employee or salary data", None),
        ],
        "result": None,
    },
    "sql_guard_retry": {
        # First plan sneaks in a second statement; guard rejects; retry is clean.
        "model": [
            _triage(True, "answerable"),
            _plan(
                "SELECT count(*) AS n FROM orders; DROP TABLE orders",
                "Order count", "metric",
                {"x": None, "y": None, "series": None, "value": "n",
                 "label": None, "value_format": "number"},
            ),
            _plan(
                "SELECT count(*) AS n FROM orders",
                "Order count", "metric",
                {"x": None, "y": None, "series": None, "value": "n",
                 "label": None, "value_format": "number"},
            ),
        ],
        "result": MockResult(columns=[("n", "int")], rows=[{"n": 4000}]),
    },
    "spec_retry": {
        # First plan claims a line chart whose x column isn't in the result;
        # spec validation fails; retry corrects the encoding.
        "model": [
            _triage(True, "answerable"),
            _plan(
                "SELECT p.category AS category, SUM(oi.quantity * oi.unit_price) AS revenue "
                "FROM order_items oi JOIN products p ON p.id = oi.product_id GROUP BY 1",
                "Revenue by category", "line",
                {"x": "month", "y": "revenue", "series": None,
                 "value": None, "label": None, "value_format": "currency"},
            ),
            _plan(
                "SELECT p.category AS category, SUM(oi.quantity * oi.unit_price) AS revenue "
                "FROM order_items oi JOIN products p ON p.id = oi.product_id GROUP BY 1",
                "Revenue by category", "bar",
                {"x": "category", "y": "revenue", "series": None,
                 "value": None, "label": None, "value_format": "currency"},
            ),
        ],
        "result": MockResult(
            columns=[("category", "text"), ("revenue", "numeric")],
            rows=[{"category": "office_supplies", "revenue": 3200.0}],
        ),
    },
    "model_api_error": {
        "model": [anthropic.AnthropicError("simulated rate limit / outage")],
        "result": None,
    },
}
