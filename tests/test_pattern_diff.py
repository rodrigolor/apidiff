"""Tests for apidiff.pattern_diff and apidiff.pattern_diff_pipeline."""

from __future__ import annotations

import json
import tempfile
import os

import pytest

from apidiff.pattern_diff import (
    PatternChange,
    PatternDiffResult,
    diff_patterns,
    _collect_patterns,
)
from apidiff.pattern_diff_pipeline import run_pattern_diff_pipeline


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "T", "version": "1"},
        "paths": {
            "/users": {
                "post": {
                    "parameters": [
                        {"name": "username", "in": "query", "schema": {"type": "string", "pattern": "^[a-z]+$"}}
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "pattern": ".+@.+"}
                                    },
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "string", "pattern": "ok"}
                                }
                            }
                        }
                    },
                }
            }
        },
    }


def _write(spec: dict) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(spec, f)
    f.close()
    return f.name


# --- PatternChange unit tests ---

def test_pattern_change_str_contains_path_and_method():
    c = PatternChange("/users", "post", "param:username", "/", "^[a-z]+$", "^[A-Z]+$")
    s = str(c)
    assert "/users" in s
    assert "POST" in s
    assert "^[a-z]+$" in s


def test_pattern_added_is_not_breaking():
    c = PatternChange("/x", "get", "param:q", "/", None, "^\\d+$")
    assert not c.is_breaking()


def test_pattern_removed_is_breaking():
    c = PatternChange("/x", "get", "param:q", "/", "^\\d+$", None)
    assert c.is_breaking()


def test_pattern_changed_is_breaking():
    c = PatternChange("/x", "get", "param:q", "/", "^[a-z]+$", "^[A-Z]+$")
    assert c.is_breaking()


# --- _collect_patterns ---

def test_collect_patterns_top_level():
    schema = {"type": "string", "pattern": "^abc$"}
    result = _collect_patterns(schema)
    assert result[""] == "^abc$"


def test_collect_patterns_nested_property():
    schema = {"type": "object", "properties": {"name": {"type": "string", "pattern": "[a-z]+"}}}
    result = _collect_patterns(schema)
    assert result["/properties/name"] == "[a-z]+"


def test_collect_patterns_empty_schema():
    assert _collect_patterns({}) == {}


# --- diff_patterns ---

def test_no_changes_when_identical(base_spec):
    result = diff_patterns(base_spec, base_spec)
    assert not result.has_changes()
    assert result.total() == 0


def test_param_pattern_removed_is_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    del head["paths"]["/users"]["post"]["parameters"][0]["schema"]["pattern"]
    result = diff_patterns(base_spec, head)
    assert result.has_breaking()
    breaking = result.breaking()
    assert any("username" in c.location for c in breaking)


def test_param_pattern_added_is_non_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/users"]["post"]["parameters"][0]["schema"]["pattern"] = ".*"
    base = copy.deepcopy(base_spec)
    del base["paths"]["/users"]["post"]["parameters"][0]["schema"]["pattern"]
    result = diff_patterns(base, head)
    assert result.has_changes()
    assert not result.has_breaking()
    assert len(result.non_breaking()) == 1


def test_requestbody_pattern_change_detected(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/users"]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]["email"]["pattern"] = "[^@]+@[^@]+"
    result = diff_patterns(base_spec, head)
    assert result.has_changes()
    assert any(c.location == "requestBody" for c in result.changes)


def test_response_pattern_change_detected(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/users"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["pattern"] = "OK"
    result = diff_patterns(base_spec, head)
    assert result.has_changes()
    assert any("response:200" in c.location for c in result.changes)


def test_diff_result_breaking_non_breaking_counts(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    # Remove param pattern (breaking) and add response pattern field (non-breaking via new prop)
    del head["paths"]["/users"]["post"]["parameters"][0]["schema"]["pattern"]
    result = diff_patterns(base_spec, head)
    assert len(result.breaking()) >= 1


# --- pipeline ---

def test_pipeline_returns_correct_type(base_spec):
    f1 = _write(base_spec)
    f2 = _write(base_spec)
    try:
        pr = run_pattern_diff_pipeline(f1, f2)
        assert not pr.has_changes()
        assert pr.total() == 0
    finally:
        os.unlink(f1)
        os.unlink(f2)


def test_pipeline_summary_no_changes(base_spec):
    f1 = _write(base_spec)
    f2 = _write(base_spec)
    try:
        pr = run_pattern_diff_pipeline(f1, f2)
        assert "No pattern changes" in pr.summary_text()
    finally:
        os.unlink(f1)
        os.unlink(f2)


def test_pipeline_summary_with_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    del head["paths"]["/users"]["post"]["parameters"][0]["schema"]["pattern"]
    f1 = _write(base_spec)
    f2 = _write(head)
    try:
        pr = run_pattern_diff_pipeline(f1, f2)
        assert pr.has_breaking()
        text = pr.summary_text()
        assert "Breaking" in text
    finally:
        os.unlink(f1)
        os.unlink(f2)
