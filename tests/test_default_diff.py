"""Tests for apidiff.default_diff."""

import pytest
from apidiff.default_diff import DefaultChange, DefaultDiffResult, diff_defaults


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                    ]
                },
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "default": {"active": True}}
                            }
                        }
                    }
                },
            }
        },
    }


def test_no_changes_when_identical(base_spec):
    result = diff_defaults(base_spec, base_spec)
    assert not result.has_changes()
    assert result.total() == 0


def test_param_default_changed(base_spec):
    head = {
        "openapi": "3.0.0",
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 50}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                    ]
                },
                "post": base_spec["paths"]["/items"]["post"],
            }
        },
    }
    result = diff_defaults(base_spec, head)
    assert result.has_changes()
    assert result.total() == 1
    change = result.changes[0]
    assert change.path == "/items"
    assert change.method == "get"
    assert change.location == "param:limit"
    assert change.old_default == 20
    assert change.new_default == 50


def test_request_body_default_changed(base_spec):
    head = {
        "openapi": "3.0.0",
        "paths": {
            "/items": {
                "get": base_spec["paths"]["/items"]["get"],
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "default": {"active": False}}
                            }
                        }
                    }
                },
            }
        },
    }
    result = diff_defaults(base_spec, head)
    assert result.has_changes()
    assert result.total() == 1
    change = result.changes[0]
    assert change.location == "requestBody:application/json"
    assert change.old_default == {"active": True}
    assert change.new_default == {"active": False}


def test_default_change_is_not_breaking(base_spec):
    head = {
        "openapi": "3.0.0",
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 100}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                    ]
                },
                "post": base_spec["paths"]["/items"]["post"],
            }
        },
    }
    result = diff_defaults(base_spec, head)
    for change in result.changes:
        assert not change.is_breaking()


def test_default_change_str():
    change = DefaultChange(
        path="/users",
        method="get",
        location="param:page",
        old_default=1,
        new_default=0,
    )
    text = str(change)
    assert "/users" in text
    assert "GET" in text
    assert "param:page" in text
    assert "1" in text
    assert "0" in text


def test_no_changes_empty_specs():
    result = diff_defaults({}, {})
    assert not result.has_changes()
    assert result.total() == 0
