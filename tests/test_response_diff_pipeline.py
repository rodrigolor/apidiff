"""Tests for apidiff.response_diff_pipeline."""
import json
import os
import pytest
from apidiff.response_diff_pipeline import (
    ResponseDiffPipelineResult,
    run_response_diff_pipeline,
    format_pipeline_result,
)


def _write(tmp_path, name, spec):
    p = tmp_path / name
    p.write_text(json.dumps(spec))
    return str(p)


@pytest.fixture
def base_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "T", "version": "1"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK"},
                        "404": {"description": "Not found"},
                    }
                }
            }
        },
    }
    return _write(tmp_path, "base.json", spec)


@pytest.fixture
def head_removed_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "T", "version": "2"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK"},
                    }
                }
            }
        },
    }
    return _write(tmp_path, "head.json", spec)


@pytest.fixture
def head_identical_file(tmp_path, base_file):
    import shutil
    dest = str(tmp_path / "head_identical.json")
    shutil.copy(base_file, dest)
    return dest


def test_pipeline_returns_result_type(base_file, head_identical_file):
    result = run_response_diff_pipeline(base_file, head_identical_file)
    assert isinstance(result, ResponseDiffPipelineResult)


def test_pipeline_no_changes_when_identical(base_file, head_identical_file):
    result = run_response_diff_pipeline(base_file, head_identical_file)
    assert not result.has_changes
    assert result.total == 0


def test_pipeline_detects_breaking_removal(base_file, head_removed_file):
    result = run_response_diff_pipeline(base_file, head_removed_file)
    assert result.has_breaking
    assert result.has_changes


def test_format_no_changes(base_file, head_identical_file):
    result = run_response_diff_pipeline(base_file, head_identical_file)
    text = format_pipeline_result(result)
    assert "No response changes" in text


def test_format_with_changes(base_file, head_removed_file):
    result = run_response_diff_pipeline(base_file, head_removed_file)
    text = format_pipeline_result(result)
    assert "BREAKING" in text
    assert "404" in text
