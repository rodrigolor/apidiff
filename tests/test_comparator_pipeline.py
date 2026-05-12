"""Tests for apidiff.comparator_pipeline."""

import json
import os
import tempfile

import pytest

from apidiff.comparator_pipeline import run_comparator_pipeline, ComparatorPipelineResult


BASE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0"},
    "paths": {
        "/users": {
            "get": {"summary": "List users", "responses": {"200": {"description": "OK"}}},
            "delete": {"summary": "Delete user", "responses": {"200": {"description": "OK"}}},
        }
    },
}

HEAD_SPEC_REMOVED = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.1"},
    "paths": {
        "/users": {
            "get": {"summary": "List users", "responses": {"200": {"description": "OK"}}},
        }
    },
}


def _write_spec(spec: dict) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(spec, f)
    f.close()
    return f.name


@pytest.fixture
def base_file():
    path = _write_spec(BASE_SPEC)
    yield path
    os.unlink(path)


@pytest.fixture
def head_removed_file():
    path = _write_spec(HEAD_SPEC_REMOVED)
    yield path
    os.unlink(path)


@pytest.fixture
def head_identical_file():
    path = _write_spec(BASE_SPEC)
    yield path
    os.unlink(path)


def test_pipeline_returns_result_type(base_file, head_removed_file):
    result = run_comparator_pipeline(base_file, head_removed_file)
    assert isinstance(result, ComparatorPipelineResult)


def test_pipeline_detects_breaking(base_file, head_removed_file):
    result = run_comparator_pipeline(base_file, head_removed_file)
    assert result.has_breaking is True


def test_pipeline_no_changes_identical(base_file, head_identical_file):
    result = run_comparator_pipeline(base_file, head_identical_file)
    assert result.has_changes is False


def test_pipeline_text_not_empty_on_changes(base_file, head_removed_file):
    result = run_comparator_pipeline(base_file, head_removed_file)
    assert result.text != "No changes detected."


def test_pipeline_text_no_changes_message(base_file, head_identical_file):
    result = run_comparator_pipeline(base_file, head_identical_file)
    assert result.text == "No changes detected."


def test_pipeline_breaking_only_flag(base_file, head_removed_file):
    result = run_comparator_pipeline(base_file, head_removed_file, breaking_only=True)
    for ep in result.report.endpoints:
        assert ep.has_breaking
