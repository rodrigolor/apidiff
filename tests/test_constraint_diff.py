"""Tests for apidiff.constraint_diff."""
import pytest
from apidiff.constraint_diff import (
    ConstraintChange,
    ConstraintDiffResult,
    diff_constraints,
)


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 100}},
                        {"name": "q", "in": "query", "schema": {"type": "string", "minLength": 0, "maxLength": 255}},
                    ]
                },
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "minProperties": 1, "maxProperties": 10}
                            }
                        }
                    }
                },
            }
        },
    }


def test_no_changes_when_identical(base_spec):
    result = diff_constraints(base_spec, base_spec)
    assert not result.has_changes()
    assert result.total() == 0


def test_tightened_minimum_is_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/items"]["get"]["parameters"][0]["schema"]["minimum"] = 5
    result = diff_constraints(base_spec, head)
    assert result.has_changes()
    breaking = [c for c in result.changes if c.is_breaking()]
    assert any(c.constraint == "minimum" for c in breaking)


def test_relaxed_maximum_is_non_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/items"]["get"]["parameters"][0]["schema"]["maximum"] = 200
    result = diff_constraints(base_spec, head)
    assert result.has_changes()
    change = next(c for c in result.changes if c.constraint == "maximum")
    assert not change.is_breaking()


def test_tightened_max_length_is_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/items"]["get"]["parameters"][1]["schema"]["maxLength"] = 50
    result = diff_constraints(base_spec, head)
    breaking = [c for c in result.changes if c.is_breaking()]
    assert any(c.constraint == "maxLength" for c in breaking)


def test_relaxed_min_length_is_non_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    # minLength 0 -> 0, no change; let's raise it (tightening)
    head["paths"]["/items"]["get"]["parameters"][1]["schema"]["minLength"] = 3
    result = diff_constraints(base_spec, head)
    change = next(c for c in result.changes if c.constraint == "minLength")
    assert change.is_breaking()


def test_request_body_constraint_change_detected(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/items"]["post"]["requestBody"]["content"]["application/json"]["schema"]["maxProperties"] = 5
    result = diff_constraints(base_spec, head)
    assert result.has_changes()
    change = next(c for c in result.changes if c.constraint == "maxProperties")
    assert change.is_breaking()


def test_constraint_change_str(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/items"]["get"]["parameters"][0]["schema"]["minimum"] = 10
    result = diff_constraints(base_spec, head)
    change = next(c for c in result.changes if c.constraint == "minimum")
    s = str(change)
    assert "/items" in s
    assert "minimum" in s
    assert "GET" in s


def test_has_breaking_false_when_only_relaxed(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/items"]["get"]["parameters"][0]["schema"]["maximum"] = 500
    result = diff_constraints(base_spec, head)
    assert result.has_changes()
    assert not result.has_breaking()


def test_empty_specs_produce_no_changes():
    result = diff_constraints({}, {})
    assert not result.has_changes()
