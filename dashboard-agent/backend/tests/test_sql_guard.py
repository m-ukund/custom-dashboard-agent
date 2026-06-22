import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import sql_guard


def test_allows_plain_select_and_adds_limit():
    out = sql_guard.sanitize("SELECT 1 AS n", max_rows=100)
    assert out.lower().startswith("select")
    assert "limit 100" in out.lower()


def test_allows_cte():
    sql = "WITH t AS (SELECT 1 AS n) SELECT * FROM t"
    out = sql_guard.sanitize(sql, max_rows=50)
    assert "limit 50" in out.lower()


def test_keeps_existing_limit():
    out = sql_guard.sanitize("SELECT * FROM orders LIMIT 5", max_rows=100)
    assert out.lower().count("limit") == 1
    assert "limit 5" in out.lower()


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE orders",
        "DELETE FROM orders",
        "UPDATE orders SET status='x'",
        "INSERT INTO orders VALUES (1)",
        "DROP TABLE orders",
        "TRUNCATE orders",
        "SELECT * FROM pg_catalog.pg_tables",
        "SELECT * FROM information_schema.tables",
        "CREATE TABLE x (id int)",
        "",
    ],
)
def test_rejects_unsafe(sql):
    with pytest.raises(sql_guard.UnsafeSQLError):
        sql_guard.sanitize(sql, max_rows=100)


def test_column_named_like_keyword_is_allowed():
    # "updated_at" / "status" must not trip the UPDATE / SET keyword guards.
    out = sql_guard.sanitize(
        "SELECT status, count(*) AS n FROM orders GROUP BY status", max_rows=100
    )
    assert "group by status" in out.lower()
