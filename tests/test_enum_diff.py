"""Tests for apidiff.enum_diff."""
import pytest
from apidiff.enum_diff import EnumChange, EnumDiffResult, diff_enums


@pytest.fixture
def base_spec():
    return {
        "paths": {
            "/orders": {
                "get": {
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["pending", "active", "closed"]},
                        }
                    ]
                }
            }
        }
    }


def test_no_changes_when_identical(base_spec):
    result = diff_enums(base_spec, base_spec)
    assert not result.has_changes()
    assert result.total() == 0


def test_enum_value_removed_is_breaking(base_spec):
    head = {
        "paths": {
            "/orders": {
                "get": {
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["pending", "active"]},
                        }
                    ]
                }
            }
        }
    }
    result = diff_enums(base_spec, head)
    assert result.has_changes()
    assert result.has_breaking()
    assert result.total() == 1
    change = result.changes[0]
    assert "closed" in change.removed
    assert change.is_breaking()


def test_enum_value_added_is_non_breaking(base_spec):
    head = {
        "paths": {
            "/orders": {
                "get": {
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["pending", "active", "closed", "archived"]},
                        }
                    ]
                }
            }
        }
    }
    result = diff_enums(base_spec, head)
    assert result.has_changes()
    assert not result.has_breaking()
    change = result.changes[0]
    assert "archived" in change.added
    assert not change.is_breaking()


def test_enum_change_str_contains_path_and_method(base_spec):
    head = {
        "paths": {
            "/orders": {
                "get": {
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["pending"]},
                        }
                    ]
                }
            }
        }
    }
    result = diff_enums(base_spec, head)
    text = str(result.changes[0])
    assert "/orders" in text
    assert "GET" in text
    assert "param:status" in text


def test_no_changes_when_paths_empty():
    result = diff_enums({"paths": {}}, {"paths": {}})
    assert not result.has_changes()


def test_enum_diff_result_defaults():
    r = EnumDiffResult()
    assert not r.has_changes()
    assert not r.has_breaking()
    assert r.total() == 0
