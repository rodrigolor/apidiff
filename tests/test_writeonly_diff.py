"""Tests for apidiff.writeonly_diff."""

import pytest
from apidiff.writeonly_diff import WriteOnlyChange, WriteOnlyDiffResult, diff_writeonly


@pytest.fixture
def base_spec():
    return {
        "paths": {
            "/items": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "properties": {
                                        "password": {"type": "string", "writeOnly": True},
                                        "name": {"type": "string"},
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "token": {"type": "string"},
                                        }
                                    }
                                }
                            }
                        }
                    },
                }
            }
        }
    }


def test_no_changes_when_identical(base_spec):
    result = diff_writeonly(base_spec, base_spec)
    assert not result.has_changes()
    assert result.total() == 0


def test_request_writeonly_removed_is_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    props = head["paths"]["/items"]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]
    del props["password"]["writeOnly"]  # effectively None now
    result = diff_writeonly(base_spec, head)
    assert result.has_changes()
    breaking = result.breaking_changes()
    assert any(c.field == "password" for c in breaking)


def test_response_writeonly_added_is_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    props = head["paths"]["/items"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]
    props["token"]["writeOnly"] = True
    result = diff_writeonly(base_spec, head)
    assert result.has_breaking()
    assert any(c.field == "token" and c.is_breaking() for c in result.changes)


def test_response_writeonly_removed_is_non_breaking(base_spec):
    import copy
    base = copy.deepcopy(base_spec)
    base["paths"]["/items"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["token"]["writeOnly"] = True
    head = copy.deepcopy(base)
    del head["paths"]["/items"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["token"]["writeOnly"]
    result = diff_writeonly(base, head)
    assert result.has_changes()
    assert not result.has_breaking()


def test_writeonly_change_str_request():
    change = WriteOnlyChange(
        path="/items", method="post", field="password",
        location="request", status_code=None,
        old_value=True, new_value=None,
    )
    s = str(change)
    assert "/items" in s
    assert "password" in s
    assert "request" in s


def test_writeonly_change_str_response_with_status():
    change = WriteOnlyChange(
        path="/items", method="get", field="token",
        location="response", status_code="200",
        old_value=None, new_value=True,
    )
    s = str(change)
    assert "200" in s
    assert "token" in s


def test_diff_result_breaking_changes_filter(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    props = head["paths"]["/items"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]
    props["token"]["writeOnly"] = True
    result = diff_writeonly(base_spec, head)
    assert len(result.breaking_changes()) == len([c for c in result.changes if c.is_breaking()])
