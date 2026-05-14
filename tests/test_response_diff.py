"""Tests for apidiff.response_diff."""
import pytest
from apidiff.differ import ChangeType
from apidiff.response_diff import (
    ResponseChange,
    diff_responses,
    is_breaking_response_change,
)


@pytest.fixture
def base_spec():
    return {
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK", "schema": {"type": "array"}},
                        "404": {"description": "Not found"},
                    }
                }
            }
        }
    }


@pytest.fixture
def head_spec_no_changes(base_spec):
    import copy
    return copy.deepcopy(base_spec)


@pytest.fixture
def head_spec_removed_404():
    return {
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK", "schema": {"type": "array"}},
                    }
                }
            }
        }
    }


@pytest.fixture
def head_spec_added_500():
    return {
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK", "schema": {"type": "array"}},
                        "404": {"description": "Not found"},
                        "500": {"description": "Server error"},
                    }
                }
            }
        }
    }


def test_no_changes_when_identical(base_spec, head_spec_no_changes):
    result = diff_responses(base_spec, head_spec_no_changes)
    assert result == []


def test_removed_response_code_detected(base_spec, head_spec_removed_404):
    result = diff_responses(base_spec, head_spec_removed_404)
    assert any(r.status_code == "404" and r.change_type == ChangeType.REMOVED for r in result)


def test_added_response_code_detected(base_spec, head_spec_added_500):
    result = diff_responses(base_spec, head_spec_added_500)
    assert any(r.status_code == "500" and r.change_type == ChangeType.ADDED for r in result)


def test_removed_response_is_breaking(base_spec, head_spec_removed_404):
    result = diff_responses(base_spec, head_spec_removed_404)
    breaking = [r for r in result if is_breaking_response_change(r)]
    assert len(breaking) == 1
    assert breaking[0].status_code == "404"


def test_added_response_is_not_breaking(base_spec, head_spec_added_500):
    result = diff_responses(base_spec, head_spec_added_500)
    breaking = [r for r in result if is_breaking_response_change(r)]
    assert breaking == []


def test_response_change_str_removed():
    rc = ResponseChange("/users", "get", "404", "<response>", ChangeType.REMOVED, old_value={"description": "Not found"})
    s = str(rc)
    assert "removed" in s
    assert "/users" in s
    assert "404" in s


def test_response_change_str_added():
    rc = ResponseChange("/users", "post", "201", "<response>", ChangeType.ADDED, new_value={"description": "Created"})
    s = str(rc)
    assert "added" in s
    assert "201" in s


def test_schema_field_change_detected():
    base = {"paths": {"/items": {"get": {"responses": {"200": {"schema": {"type": "array"}}}}}}}
    head = {"paths": {"/items": {"get": {"responses": {"200": {"schema": {"type": "object"}}}}}}}
    result = diff_responses(base, head)
    assert any(r.field == "type" and r.change_type == ChangeType.MODIFIED for r in result)
