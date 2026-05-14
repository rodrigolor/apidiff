"""Tests for apidiff.format_diff."""
import pytest
from apidiff.format_diff import (
    FormatChange,
    FormatDiffResult,
    diff_formats,
)


@pytest.fixture
def base_spec():
    return {
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "format": "uuid"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "string", "format": "date-time"}
                                }
                            }
                        }
                    },
                }
            }
        }
    }


def test_no_changes_when_identical(base_spec):
    result = diff_formats(base_spec, base_spec)
    assert not result.has_changes()
    assert result.total() == 0


def test_request_format_change_detected(base_spec):
    import copy

    head = copy.deepcopy(base_spec)
    head["paths"]["/users"]["post"]["requestBody"]["content"]["application/json"][
        "schema"
    ]["format"] = "email"
    result = diff_formats(base_spec, head)
    assert result.has_changes()
    breaking = [c for c in result.changes if c.location == "request"]
    assert len(breaking) == 1
    assert breaking[0].old_value == "uuid"
    assert breaking[0].new_value == "email"


def test_response_format_change_detected(base_spec):
    import copy

    head = copy.deepcopy(base_spec)
    head["paths"]["/users"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["format"] = "date"
    result = diff_formats(base_spec, head)
    resp_changes = [c for c in result.changes if c.location == "response"]
    assert len(resp_changes) == 1
    assert resp_changes[0].status_code == "200"
    assert resp_changes[0].old_value == "date-time"
    assert resp_changes[0].new_value == "date"


def test_format_removed_is_breaking(base_spec):
    import copy

    head = copy.deepcopy(base_spec)
    del head["paths"]["/users"]["post"]["requestBody"]["content"]["application/json"][
        "schema"
    ]["format"]
    result = diff_formats(base_spec, head)
    req_changes = [c for c in result.changes if c.location == "request"]
    assert len(req_changes) == 1
    assert req_changes[0].is_breaking()


def test_format_added_is_non_breaking(base_spec):
    import copy

    head = copy.deepcopy(base_spec)
    # Remove from base so head is "adding" it
    base_mod = copy.deepcopy(base_spec)
    del base_mod["paths"]["/users"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]["format"]
    result = diff_formats(base_mod, head)
    req_changes = [c for c in result.changes if c.location == "request"]
    assert len(req_changes) == 1
    assert not req_changes[0].is_breaking()


def test_has_breaking_true_when_format_removed(base_spec):
    import copy

    head = copy.deepcopy(base_spec)
    del head["paths"]["/users"]["post"]["requestBody"]["content"]["application/json"][
        "schema"
    ]["format"]
    result = diff_formats(base_spec, head)
    assert result.has_breaking()


def test_format_change_str_contains_path_and_method():
    change = FormatChange(
        path="/items",
        method="get",
        location="response",
        status_code="200",
        field="format",
        old_value="date-time",
        new_value="date",
    )
    s = str(change)
    assert "/items" in s
    assert "GET" in s
    assert "date-time" in s
    assert "date" in s


def test_empty_specs_produce_no_changes():
    result = diff_formats({"paths": {}}, {"paths": {}})
    assert not result.has_changes()
    assert not result.has_breaking()
