"""Tests for apidiff.security_diff_pipeline."""
import json
import os
import tempfile

import pytest

from apidiff.security_diff_pipeline import (
    SecurityDiffPipelineResult,
    run_security_diff_pipeline,
)


def _write(spec: dict, suffix: str = ".json") -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False
    )
    json.dump(spec, f)
    f.close()
    return f.name


@pytest.fixture
def base_file():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "T", "version": "1"},
        "paths": {},
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"}
            }
        },
    }
    path = _write(spec)
    yield path
    os.unlink(path)


@pytest.fixture
def head_removed_file():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "T", "version": "1"},
        "paths": {},
        "components": {"securitySchemes": {}},
    }
    path = _write(spec)
    yield path
    os.unlink(path)


@pytest.fixture
def head_identical_file(base_file):
    return base_file


def test_pipeline_returns_result_type(base_file, head_identical_file):
    result = run_security_diff_pipeline(base_file, head_identical_file)
    assert isinstance(result, SecurityDiffPipelineResult)


def test_pipeline_no_changes_when_identical(base_file, head_identical_file):
    result = run_security_diff_pipeline(base_file, head_identical_file)
    assert not result.has_changes
    assert not result.has_breaking
    assert result.total == 0


def test_pipeline_detects_breaking_removal(base_file, head_removed_file):
    result = run_security_diff_pipeline(base_file, head_removed_file)
    assert result.has_changes
    assert result.has_breaking
    assert result.total >= 1


def test_pipeline_summary_no_changes(base_file, head_identical_file):
    result = run_security_diff_pipeline(base_file, head_identical_file)
    assert "No security" in result.summary_text()


def test_pipeline_summary_with_changes(base_file, head_removed_file):
    result = run_security_diff_pipeline(base_file, head_removed_file)
    text = result.summary_text()
    assert "BREAKING" in text
    assert "bearerAuth" in text


def test_pipeline_stores_paths(base_file, head_removed_file):
    result = run_security_diff_pipeline(base_file, head_removed_file)
    assert result.base_path == base_file
    assert result.head_path == head_removed_file
