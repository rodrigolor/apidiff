"""Tests for apidiff.header_diff module."""
import pytest

from apidiff.differ import ChangeType
from apidiff.header_diff import HeaderChange, diff_headers


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_spec():
    return {
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "X-Request-ID", "in": "header", "required": False},
                        {"name": "X-Tenant", "in": "header", "required": True},
                    ],
                    "responses": {
                        "200": {
                            "headers": {
                                "X-Rate-Limit": {"schema": {"type": "integer"}},
                            }
                        }
                    },
                }
            }
        }
    }


# ---------------------------------------------------------------------------
# HeaderChange.__str__
# ---------------------------------------------------------------------------

def test_header_change_str_with_status_code():
    change = HeaderChange("/items", "get", "response", "200", "X-Rate-Limit",
                          ChangeType.NON_BREAKING, "response header removed")
    text = str(change)
    assert "response(200)" in text
    assert "X-Rate-Limit" in text


def test_header_change_str_request_no_status_code():
    change = HeaderChange("/items", "get", "request", None, "X-Tenant",
                          ChangeType.BREAKING, "required header parameter removed")
    text = str(change)
    assert "request" in text
    assert "(" not in text.split("request")[1].split(" ")[0]


def test_header_change_is_breaking_true():
    change = HeaderChange("/a", "post", "request", None, "H",
                          ChangeType.BREAKING, "removed")
    assert change.is_breaking is True


def test_header_change_is_breaking_false():
    change = HeaderChange("/a", "post", "response", "200", "H",
                          ChangeType.NON_BREAKING, "added")
    assert change.is_breaking is False


# ---------------------------------------------------------------------------
# diff_headers — no changes
# ---------------------------------------------------------------------------

def test_no_changes_when_identical(base_spec):
    changes = diff_headers(base_spec, base_spec, "/items", "get")
    assert changes == []


# ---------------------------------------------------------------------------
# Request header changes
# ---------------------------------------------------------------------------

def test_required_request_header_removed_is_breaking(base_spec):
    head = {
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "X-Request-ID", "in": "header", "required": False},
                        # X-Tenant removed
                    ],
                    "responses": {"200": {"headers": {"X-Rate-Limit": {}}}},
                }
            }
        }
    }
    changes = diff_headers(base_spec, head, "/items", "get")
    breaking = [c for c in changes if c.is_breaking]
    assert any(c.header_name == "X-Tenant" for c in breaking)


def test_new_required_request_header_is_breaking(base_spec):
    head_spec = {
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "X-Request-ID", "in": "header", "required": True},  # now required
                        {"name": "X-Tenant", "in": "header", "required": True},
                    ],
                    "responses": {"200": {"headers": {"X-Rate-Limit": {}}}},
                }
            }
        }
    }
    changes = diff_headers(base_spec, head_spec, "/items", "get")
    breaking = [c for c in changes if c.is_breaking and c.header_name == "X-Request-ID"]
    assert len(breaking) == 1


def test_new_optional_request_header_is_non_breaking(base_spec):
    head_spec = {
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "X-Request-ID", "in": "header", "required": False},
                        {"name": "X-Tenant", "in": "header", "required": True},
                        {"name": "X-New-Header", "in": "header", "required": False},
                    ],
                    "responses": {"200": {"headers": {"X-Rate-Limit": {}}}},
                }
            }
        }
    }
    changes = diff_headers(base_spec, head_spec, "/items", "get")
    new_header = [c for c in changes if c.header_name == "X-New-Header"]
    assert len(new_header) == 1
    assert new_header[0].change_type == ChangeType.NON_BREAKING


# ---------------------------------------------------------------------------
# Response header changes
# ---------------------------------------------------------------------------

def test_response_header_removed_is_non_breaking(base_spec):
    head_spec = {
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "X-Request-ID", "in": "header", "required": False},
                        {"name": "X-Tenant", "in": "header", "required": True},
                    ],
                    "responses": {"200": {}},  # X-Rate-Limit header removed
                }
            }
        }
    }
    changes = diff_headers(base_spec, head_spec, "/items", "get")
    removed = [c for c in changes if c.header_name == "X-Rate-Limit"]
    assert len(removed) == 1
    assert removed[0].change_type == ChangeType.NON_BREAKING


def test_response_header_added_is_non_breaking(base_spec):
    head_spec = {
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "X-Request-ID", "in": "header", "required": False},
                        {"name": "X-Tenant", "in": "header", "required": True},
                    ],
                    "responses": {
                        "200": {
                            "headers": {
                                "X-Rate-Limit": {},
                                "X-Retry-After": {},
                            }
                        }
                    },
                }
            }
        }
    }
    changes = diff_headers(base_spec, head_spec, "/items", "get")
    added = [c for c in changes if c.header_name == "X-Retry-After"]
    assert len(added) == 1
    assert added[0].change_type == ChangeType.NON_BREAKING


def test_missing_path_returns_empty():
    spec = {"paths": {}}
    changes = diff_headers(spec, spec, "/nonexistent", "get")
    assert changes == []
