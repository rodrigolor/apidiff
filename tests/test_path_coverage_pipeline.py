"""Tests for apidiff.path_coverage_pipeline."""

import json
import pytest
from pathlib import Path

from apidiff.path_coverage_pipeline import run_coverage_pipeline, CoveragePipelineResult


_BASE = {
    "openapi": "3.0.0",
    "info": {"title": "API", "version": "1.0"},
    "paths": {
        "/pets": {"get": {"responses": {"200": {"description": "ok"}}}},
        "/pets/{id}": {"delete": {"responses": {"204": {"description": "deleted"}}}},
    },
}

_HEAD_REMOVED = {
    "openapi": "3.0.0",
    "info": {"title": "API", "version": "2.0"},
    "paths": {
        "/pets": {"get": {"responses": {"200": {"description": "ok"}}}},
    },
}

_HEAD_IDENTICAL = {
    "openapi": "3.0.0",
    "info": {"title": "API", "version": "1.0"},
    "paths": {
        "/pets": {"get": {"responses": {"200": {"description": "ok"}}}},
        "/pets/{id}": {"delete": {"responses": {"204": {"description": "deleted"}}}},
    },
}


def _write(tmp_path: Path, name: str, data: dict) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return str(p)


def test_pipeline_returns_correct_type(tmp_path):
    base = _write(tmp_path, "base.json", _BASE)
    head = _write(tmp_path, "head.json", _HEAD_REMOVED)
    result = run_coverage_pipeline(base, head)
    assert isinstance(result, CoveragePipelineResult)


def test_pipeline_has_changes_when_endpoint_removed(tmp_path):
    base = _write(tmp_path, "base.json", _BASE)
    head = _write(tmp_path, "head.json", _HEAD_REMOVED)
    result = run_coverage_pipeline(base, head)
    assert result.has_changes


def test_pipeline_no_changes_when_identical(tmp_path):
    base = _write(tmp_path, "base.json", _BASE)
    head = _write(tmp_path, "head.json", _HEAD_IDENTICAL)
    result = run_coverage_pipeline(base, head)
    assert not result.has_changes


def test_pipeline_stores_paths(tmp_path):
    base = _write(tmp_path, "base.json", _BASE)
    head = _write(tmp_path, "head.json", _HEAD_REMOVED)
    result = run_coverage_pipeline(base, head)
    assert result.base_path == base
    assert result.head_path == head


def test_pipeline_summary_text_is_string(tmp_path):
    base = _write(tmp_path, "base.json", _BASE)
    head = _write(tmp_path, "head.json", _HEAD_REMOVED)
    result = run_coverage_pipeline(base, head)
    assert isinstance(result.summary_text, str)
    assert len(result.summary_text) > 0
