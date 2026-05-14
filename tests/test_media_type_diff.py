"""Tests for apidiff.media_type_diff."""
import pytest
from apidiff.media_type_diff import (
    MediaTypeChange,
    MediaTypeDiffResult,
    diff_media_types,
)


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}},
                            "application/xml": {"schema": {"type": "object"}},
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            }
                        }
                    },
                }
            }
        },
    }


def test_no_changes_when_identical(base_spec):
    result = diff_media_types(base_spec, base_spec)
    assert not result.has_changes()
    assert result.total() == 0


def test_request_media_type_removed_is_breaking(base_spec):
    head = {
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {"application/json": {"schema": {"type": "object"}}}
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            }
                        }
                    },
                }
            }
        }
    }
    result = diff_media_types(base_spec, head)
    assert result.has_changes()
    assert result.has_breaking()
    removed = [c for c in result.changes if c.change_kind == "removed"]
    assert any(c.media_type == "application/xml" for c in removed)


def test_request_media_type_added_is_non_breaking(base_spec):
    head_spec = {
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {},
                            "application/xml": {},
                            "text/plain": {},
                        }
                    },
                    "responses": {
                        "200": {"content": {"application/json": {}}}
                    },
                }
            }
        }
    }
    result = diff_media_types(base_spec, head_spec)
    added = [c for c in result.changes if c.change_kind == "added"]
    assert any(c.media_type == "text/plain" for c in added)
    assert not result.has_breaking()


def test_response_media_type_removed_is_breaking(base_spec):
    head = {
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {},
                            "application/xml": {},
                        }
                    },
                    "responses": {"200": {}},
                }
            }
        }
    }
    result = diff_media_types(base_spec, head)
    assert result.has_breaking()
    removed = [c for c in result.changes if c.change_kind == "removed" and c.location == "200"]
    assert len(removed) == 1
    assert removed[0].media_type == "application/json"


def test_media_type_change_str_contains_key_info():
    change = MediaTypeChange(
        path="/items",
        method="get",
        location="200",
        change_kind="removed",
        media_type="application/json",
    )
    s = str(change)
    assert "REMOVED" in s
    assert "application/json" in s
    assert "/items" in s
    assert "GET" in s


def test_media_type_change_is_breaking_removed():
    c = MediaTypeChange("/a", "post", "request", "removed", "application/json")
    assert c.is_breaking() is True


def test_media_type_change_is_not_breaking_added():
    c = MediaTypeChange("/a", "post", "request", "added", "text/plain")
    assert c.is_breaking() is False


def test_diff_result_has_changes_false_when_empty():
    result = MediaTypeDiffResult(changes=[])
    assert not result.has_changes()
    assert result.total() == 0
