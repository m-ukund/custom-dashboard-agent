import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pydantic import ValidationError

from models import Encoding, WidgetSpec


def _spec(**overrides):
    base = dict(
        id="abc",
        title="T",
        request="r",
        type="bar",
        sql="SELECT a, b FROM t",
        columns=[{"name": "a", "dtype": "text"}, {"name": "b", "dtype": "int"}],
        data=[{"a": "x", "b": 1}],
        encoding=Encoding(x="a", y="b"),
    )
    base.update(overrides)
    return WidgetSpec(**base)


def test_valid_bar_spec():
    spec = _spec()
    assert spec.type.value == "bar"


def test_chart_requires_axes():
    with pytest.raises(ValidationError):
        _spec(encoding=Encoding(x="a"))  # missing y


def test_chart_encoding_must_reference_real_columns():
    with pytest.raises(ValidationError):
        _spec(encoding=Encoding(x="a", y="nonexistent"))


def test_metric_requires_value():
    with pytest.raises(ValidationError):
        _spec(type="metric", encoding=Encoding())


def test_metric_value_must_be_real_column():
    with pytest.raises(ValidationError):
        _spec(type="metric", encoding=Encoding(value="ghost"))


def test_table_accepts_any_columns():
    spec = _spec(type="table", encoding=Encoding())
    assert spec.type.value == "table"
