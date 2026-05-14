"""Tests for apidiff.security_diff."""
import pytest
from apidiff.security_diff import (
    SecurityChange,
    SecurityDiffResult,
    diff_security,
)


@pytest.fixture
def base_spec():
    return {
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"},
                "apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            }
        }
    }


def test_no_changes_when_identical(base_spec):
    result = diff_security(base_spec, base_spec)
    assert not result.has_changes
    assert not result.has_breaking


def test_scheme_removed_is_breaking(base_spec):
    head = {"components": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}}}}
    result = diff_security(base_spec, head)
    assert result.has_changes
    assert result.has_breaking
    removed = [c for c in result.changes if c.change_type == "removed"]
    assert len(removed) == 1
    assert removed[0].scheme_name == "apiKey"


def test_scheme_added_is_non_breaking(base_spec):
    head_schemes = dict(base_spec["components"]["securitySchemes"])
    head_schemes["oauth2"] = {"type": "oauth2"}
    head = {"components": {"securitySchemes": head_schemes}}
    result = diff_security(base_spec, head)
    assert result.has_changes
    assert not result.has_breaking
    added = [c for c in result.changes if c.change_type == "added"]
    assert any(c.scheme_name == "oauth2" for c in added)


def test_scheme_type_change_is_breaking(base_spec):
    head = {
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "apiKey", "scheme": "bearer"},
                "apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            }
        }
    }
    result = diff_security(base_spec, head)
    assert result.has_breaking
    modified = [c for c in result.changes if c.change_type == "modified" and c.field == "type"]
    assert len(modified) == 1
    assert modified[0].is_breaking()


def test_non_breaking_field_change(base_spec):
    head = {
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"},
                "apiKey": {"type": "apiKey", "in": "query", "name": "X-API-Key"},
            }
        }
    }
    result = diff_security(base_spec, head)
    assert result.has_changes
    modified = [c for c in result.changes if c.change_type == "modified"]
    assert all(not c.is_breaking() for c in modified)


def test_empty_specs():
    result = diff_security({}, {})
    assert not result.has_changes


def test_security_change_str_removed():
    c = SecurityChange(scheme_name="myKey", change_type="removed")
    assert "myKey" in str(c)
    assert "removed" in str(c)
    assert "breaking" in str(c)


def test_security_change_str_added():
    c = SecurityChange(scheme_name="newKey", change_type="added")
    assert "newKey" in str(c)
    assert "added" in str(c)


def test_security_change_str_modified():
    c = SecurityChange(scheme_name="s", change_type="modified", field="scheme", old_value="basic", new_value="bearer")
    assert "scheme" in str(c)
    assert "basic" in str(c)
    assert "bearer" in str(c)
