"""Tests for the differ module."""

import pytest
from apidiff.differ import ChangeType, diff_specs


@pytest.fixture
def base_spec():
    return {
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False}
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/users/{id}": {
                "get": {
                    "parameters": [
                        {"name": "id", "in": "path", "required": True}
                    ],
                    "responses": {"200": {"description": "OK"}, "404": {"description": "Not found"}},
                },
                "delete": {
                    "parameters": [
                        {"name": "id", "in": "path", "required": True}
                    ],
                    "responses": {"204": {"description": "Deleted"}},
                },
            },
        },
    }


def test_no_changes(base_spec):
    result = diff_specs(base_spec, base_spec)
    assert not result.has_breaking_changes
    assert len(result.changes) == 0


def test_endpoint_removed(base_spec):
    new_spec = dict(base_spec)
    new_spec["paths"] = {"/users": base_spec["paths"]["/users"]}
    result = diff_specs(base_spec, new_spec)
    breaking_paths = [c.path for c in result.breaking]
    assert "/users/{id}" in breaking_paths
    assert result.has_breaking_changes


def test_endpoint_added(base_spec):
    new_spec = dict(base_spec)
    new_spec["paths"] = {**base_spec["paths"], "/orders": {"get": {"responses": {"200": {}}}}}
    result = diff_specs(base_spec, new_spec)
    non_breaking_paths = [c.path for c in result.non_breaking]
    assert "/orders" in non_breaking_paths
    assert not result.has_breaking_changes


def test_operation_removed(base_spec):
    new_spec = {"info": base_spec["info"], "paths": {
        "/users": base_spec["paths"]["/users"],
        "/users/{id}": {"get": base_spec["paths"]["/users/{id}"]["get"]},
    }}
    result = diff_specs(base_spec, new_spec)
    breaking_paths = [c.path for c in result.breaking]
    assert "/users/{id}.delete" in breaking_paths


def test_operation_added(base_spec):
    new_spec = {"info": base_spec["info"], "paths": {
        "/users": {
            "get": base_spec["paths"]["/users"]["get"],
            "post": {"responses": {"201": {"description": "Created"}}},
        },
        "/users/{id}": base_spec["paths"]["/users/{id}"],
    }}
    result = diff_specs(base_spec, new_spec)
    non_breaking_paths = [c.path for c in result.non_breaking]
    assert "/users.post" in non_breaking_paths


def test_parameter_removed(base_spec):
    new_spec = {"info": base_spec["info"], "paths": {
        "/users": {"get": {"parameters": [], "responses": {"200": {}}}},
        "/users/{id}": base_spec["paths"]["/users/{id}"],
    }}
    result = diff_specs(base_spec, new_spec)
    breaking_paths = [c.path for c in result.breaking]
    assert any("limit" in p for p in breaking_paths)


def test_parameter_became_required(base_spec):
    new_spec = {"info": base_spec["info"], "paths": {
        "/users": {
            "get": {
                "parameters": [{"name": "limit", "in": "query", "required": True}],
                "responses": {"200": {}},
            }
        },
        "/users/{id}": base_spec["paths"]["/users/{id}"],
    }}
    result = diff_specs(base_spec, new_spec)
    breaking = result.breaking
    assert any("became required" in c.message for c in breaking)


def test_version_change_is_info(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["info"]["version"] = "2.0.0"
    result = diff_specs(base_spec, new_spec)
    info_changes = [c for c in result.changes if c.change_type == ChangeType.INFO]
    assert len(info_changes) == 1
    assert "2.0.0" in info_changes[0].message


def test_response_removed_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["paths"]["/users/{id}"]["get"]["responses"]["404"]
    result = diff_specs(base_spec, new_spec)
    breaking_paths = [c.path for c in result.breaking]
    assert "/users/{id}.get.responses.404" in breaking_paths


def test_change_str_representation():
    from apidiff.differ import Change, ChangeType
    c = Change(ChangeType.BREAKING, "/foo", "endpoint removed")
    assert "[BREAKING]" in str(c)
    assert "/foo" in str(c)
