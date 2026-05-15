"""Unit tests for ConstraintChange dataclass properties."""
import pytest
from apidiff.constraint_diff import ConstraintChange


def _make(constraint: str, old, new) -> ConstraintChange:
    return ConstraintChange(
        path="/things",
        method="post",
        param_or_field="body:application/json",
        constraint=constraint,
        old_value=old,
        new_value=new,
    )


@pytest.mark.parametrize("constraint,old,new,breaking", [
    ("minimum", 0, 5, True),
    ("minimum", 5, 0, False),
    ("maximum", 100, 50, True),
    ("maximum", 50, 100, False),
    ("minLength", 0, 3, True),
    ("minLength", 3, 0, False),
    ("maxLength", 100, 20, True),
    ("maxLength", 20, 100, False),
    ("minItems", 0, 1, True),
    ("minItems", 1, 0, False),
    ("maxItems", 10, 5, True),
    ("maxItems", 5, 10, False),
    ("minProperties", 0, 2, True),
    ("maxProperties", 20, 5, True),
    ("multipleOf", None, 3, True),
    ("multipleOf", 3, None, False),
])
def test_is_breaking_parametrized(constraint, old, new, breaking):
    change = _make(constraint, old, new)
    assert change.is_breaking() == breaking


def test_str_contains_all_key_parts():
    change = _make("minimum", 0, 10)
    s = str(change)
    assert "/things" in s
    assert "POST" in s
    assert "minimum" in s
    assert "0" in s
    assert "10" in s


def test_unknown_constraint_is_not_breaking():
    change = _make("x-custom", "old", "new")
    assert not change.is_breaking()


def test_type_error_in_comparison_returns_false():
    # old_value and new_value are incomparable types
    change = _make("minimum", "abc", 5)
    assert not change.is_breaking()
