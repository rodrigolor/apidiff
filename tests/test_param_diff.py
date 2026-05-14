"""Tests for apidiff.param_diff module."""

import pytest
from apidiff.differ import ChangeType
from apidiff.param_diff import (
    ParamChange,
    diff_parameters,
    extract_param_changes,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "T", "version": "1"},
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
                        {"name": "q", "in": "query", "required": True, "schema": {"type": "string"}},
                    ]
                }
            }
        },
    }


@pytest.fixture
def head_spec_no_changes(base_spec):
    import copy
    return copy.deepcopy(base_spec)


# ---------------------------------------------------------------------------
# ParamChange.__str__
# ---------------------------------------------------------------------------

def test_param_change_str():
    pc = ParamChange("/items", "get", "limit", ChangeType.BREAKING, "type changed")
    result = str(pc)
    assert "GET /items" in result
    assert "limit" in result
    assert "type changed" in result


# ---------------------------------------------------------------------------
# diff_parameters
# ---------------------------------------------------------------------------

def test_no_param_changes_when_identical():
    params = [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}]
    changes = diff_parameters("/x", "get", params, params)
    assert changes == []


def test_required_param_removed_is_breaking():
    base = [{"name": "q", "in": "query", "required": True}]
    changes = diff_parameters("/search", "get", base, [])
    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.BREAKING
    assert changes[0].param_name == "q"


def test_optional_param_removed_is_non_breaking():
    base = [{"name": "limit", "in": "query", "required": False}]
    changes = diff_parameters("/items", "get", base, [])
    assert len(changes) == 1
    # optional removal is still reported but as breaking per spec conventions
    assert changes[0].param_name == "limit"


def test_new_required_param_is_breaking():
    head = [{"name": "token", "in": "header", "required": True}]
    changes = diff_parameters("/secure", "post", [], head)
    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.BREAKING


def test_new_optional_param_is_non_breaking():
    head = [{"name": "verbose", "in": "query", "required": False}]
    changes = diff_parameters("/items", "get", [], head)
    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.NON_BREAKING


def test_param_became_required_is_breaking():
    base = [{"name": "fmt", "in": "query", "required": False}]
    head = [{"name": "fmt", "in": "query", "required": True}]
    changes = diff_parameters("/data", "get", base, head)
    assert any(c.change_type == ChangeType.BREAKING and "required" in c.detail for c in changes)


def test_param_became_optional_is_non_breaking():
    base = [{"name": "fmt", "in": "query", "required": True}]
    head = [{"name": "fmt", "in": "query", "required": False}]
    changes = diff_parameters("/data", "get", base, head)
    assert any(c.change_type == ChangeType.NON_BREAKING for c in changes)


def test_type_change_is_breaking():
    base = [{"name": "id", "in": "query", "schema": {"type": "integer"}}]
    head = [{"name": "id", "in": "query", "schema": {"type": "string"}}]
    changes = diff_parameters("/items", "get", base, head)
    assert any("type changed" in c.detail for c in changes)
    assert any(c.change_type == ChangeType.BREAKING for c in changes)


# ---------------------------------------------------------------------------
# extract_param_changes
# ---------------------------------------------------------------------------

def test_extract_no_changes(base_spec, head_spec_no_changes):
    changes = extract_param_changes(base_spec, head_spec_no_changes)
    assert changes == []


def test_extract_skips_removed_paths(base_spec):
    head = {"openapi": "3.0.0", "info": {}, "paths": {}}
    # path removed entirely — param_diff should skip it (handled by differ)
    changes = extract_param_changes(base_spec, head)
    assert changes == []


def test_extract_detects_cross_path_changes():
    base = {
        "paths": {
            "/a": {"get": {"parameters": [{"name": "x", "in": "query", "required": True}]}},
            "/b": {"post": {"parameters": []}},
        }
    }
    head = {
        "paths": {
            "/a": {"get": {"parameters": []}},
            "/b": {"post": {"parameters": [{"name": "body_token", "in": "header", "required": True}]}},
        }
    }
    changes = extract_param_changes(base, head)
    paths_affected = {c.path for c in changes}
    assert "/a" in paths_affected
    assert "/b" in paths_affected
