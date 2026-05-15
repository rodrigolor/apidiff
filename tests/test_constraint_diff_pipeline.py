"""Tests for apidiff.constraint_diff_pipeline."""
import json
import os
import tempfile

import pytest

from apidiff.constraint_diff_pipeline import (
    ConstraintDiffPipelineResult,
    run_constraint_diff_pipeline,
)


def _write(spec: dict) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(spec, f)
    f.close()
    return f.name


BASE = {
    "openapi": "3.0.0",
    "paths": {
        "/users": {
            "get": {
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 50}}
                ]
            }
        }
    },
}

HEAD_TIGHTENED = {
    "openapi": "3.0.0",
    "paths": {
        "/users": {
            "get": {
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 10}}
                ]
            }
        }
    },
}


@pytest.fixture
def base_file():
    p = _write(BASE)
    yield p
    os.unlink(p)


@pytest.fixture
def head_tightened_file():
    p = _write(HEAD_TIGHTENED)
    yield p
    os.unlink(p)


@pytest.fixture
def head_identical_file():
    p = _write(BASE)
    yield p
    os.unlink(p)


def test_pipeline_returns_correct_type(base_file, head_identical_file):
    res = run_constraint_diff_pipeline(base_file, head_identical_file)
    assert isinstance(res, ConstraintDiffPipelineResult)


def test_pipeline_no_changes_when_identical(base_file, head_identical_file):
    res = run_constraint_diff_pipeline(base_file, head_identical_file)
    assert not res.has_changes()
    assert not res.has_breaking()


def test_pipeline_detects_breaking_change(base_file, head_tightened_file):
    res = run_constraint_diff_pipeline(base_file, head_tightened_file)
    assert res.has_changes()
    assert res.has_breaking()


def test_pipeline_total_count(base_file, head_tightened_file):
    res = run_constraint_diff_pipeline(base_file, head_tightened_file)
    assert res.total() >= 1


def test_summary_text_no_changes(base_file, head_identical_file):
    res = run_constraint_diff_pipeline(base_file, head_identical_file)
    assert "No constraint changes" in res.summary_text()


def test_summary_text_with_changes(base_file, head_tightened_file):
    res = run_constraint_diff_pipeline(base_file, head_tightened_file)
    text = res.summary_text()
    assert "BREAKING" in text
    assert "maximum" in text
