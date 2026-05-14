"""Tests for apidiff.example_diff and apidiff.example_diff_pipeline."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from apidiff.example_diff import ExampleChange, ExampleDiffResult, diff_examples
from apidiff.example_diff_pipeline import run_example_diff_pipeline


BASE_SPEC: dict = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {
        "/pets": {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "example": {"id": 1, "name": "Fido"}
                            }
                        }
                    }
                }
            },
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "examples": {
                                "dog": {"value": {"name": "Rex"}}
                            }
                        }
                    }
                },
                "responses": {}
            },
        }
    },
}


def _write(spec: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(spec, f)
    return path


def test_no_changes_when_identical():
    result = diff_examples(BASE_SPEC, BASE_SPEC)
    assert not result.has_changes()
    assert result.total() == 0


def test_example_removed_detected():
    import copy
    head = copy.deepcopy(BASE_SPEC)
    del head["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["example"]
    result = diff_examples(BASE_SPEC, head)
    assert result.has_changes()
    removed = [c for c in result.changes if c.change_type == "removed"]
    assert len(removed) == 1
    assert removed[0].path == "/pets"
    assert removed[0].method == "get"


def test_example_added_detected():
    import copy
    head = copy.deepcopy(BASE_SPEC)
    head["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["example"] = {"id": 99}
    head["paths"]["/pets"]["get"]["responses"]["404"] = {
        "content": {"application/json": {"example": {"error": "not found"}}}
    }
    result = diff_examples(BASE_SPEC, head)
    added = [c for c in result.changes if c.change_type == "added"]
    assert any(c.path == "/pets" and c.method == "get" for c in added)


def test_example_modified_detected():
    import copy
    head = copy.deepcopy(BASE_SPEC)
    head["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["example"] = {"id": 2}
    result = diff_examples(BASE_SPEC, head)
    modified = [c for c in result.changes if c.change_type == "modified"]
    assert len(modified) == 1
    assert modified[0].base_value == {"id": 1, "name": "Fido"}
    assert modified[0].head_value == {"id": 2}


def test_example_change_is_not_breaking():
    change = ExampleChange("/pets", "get", "responses/200/application/json", "example", "removed", {}, None)
    assert change.is_breaking() is False


def test_example_change_str():
    change = ExampleChange("/pets", "post", "requestBody/application/json", "example", "added", None, {})
    s = str(change)
    assert "[added]" in s
    assert "/pets" in s
    assert "POST" in s


def test_pipeline_returns_correct_type():
    base_path = _write(BASE_SPEC)
    try:
        from apidiff.example_diff_pipeline import ExampleDiffPipelineResult
        result = run_example_diff_pipeline(base_path, base_path)
        assert isinstance(result, ExampleDiffPipelineResult)
    finally:
        os.unlink(base_path)


def test_pipeline_no_changes_summary():
    base_path = _write(BASE_SPEC)
    try:
        result = run_example_diff_pipeline(base_path, base_path)
        assert "No example changes" in result.summary_text()
    finally:
        os.unlink(base_path)


def test_pipeline_summary_lists_changes():
    import copy
    head = copy.deepcopy(BASE_SPEC)
    head["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["example"] = {"id": 9}
    base_path = _write(BASE_SPEC)
    head_path = _write(head)
    try:
        result = run_example_diff_pipeline(base_path, head_path)
        summary = result.summary_text()
        assert "modified" in summary
        assert result.total() == 1
    finally:
        os.unlink(base_path)
        os.unlink(head_path)
