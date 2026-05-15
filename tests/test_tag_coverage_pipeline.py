"""Tests for apidiff.tag_coverage_pipeline."""
import json
import pathlib

import pytest

from apidiff.tag_coverage_pipeline import (
    TagCoveragePipelineResult,
    run_tag_coverage_pipeline,
)


def _write(tmp_path: pathlib.Path, name: str, spec: dict) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(spec))
    return str(p)


@pytest.fixture()
def base_file(tmp_path):
    return _write(
        tmp_path,
        "base.json",
        {
            "openapi": "3.0.0",
            "info": {"title": "Base", "version": "1"},
            "paths": {
                "/pets": {
                    "get": {
                        "tags": ["pets"],
                        "responses": {"200": {"description": "ok"}},
                    }
                }
            },
        },
    )


@pytest.fixture()
def head_untagged_file(tmp_path):
    return _write(
        tmp_path,
        "head.json",
        {
            "openapi": "3.0.0",
            "info": {"title": "Head", "version": "2"},
            "paths": {
                "/pets": {
                    "get": {
                        "responses": {"200": {"description": "ok"}},
                    }
                }
            },
        },
    )


def test_pipeline_returns_correct_type(base_file):
    result = run_tag_coverage_pipeline(base_file, base_file)
    assert isinstance(result, TagCoveragePipelineResult)


def test_pipeline_no_coverage_drop_when_identical(base_file):
    result = run_tag_coverage_pipeline(base_file, base_file)
    assert result.coverage_dropped is False


def test_pipeline_detects_coverage_drop(base_file, head_untagged_file):
    result = run_tag_coverage_pipeline(base_file, head_untagged_file)
    assert result.coverage_dropped is True


def test_pipeline_summary_text_contains_warning(base_file, head_untagged_file):
    result = run_tag_coverage_pipeline(base_file, head_untagged_file)
    assert "WARNING" in result.summary_text


def test_pipeline_summary_text_no_warning_when_stable(base_file):
    result = run_tag_coverage_pipeline(base_file, base_file)
    assert "WARNING" not in result.summary_text


def test_pipeline_stores_paths(base_file, head_untagged_file):
    result = run_tag_coverage_pipeline(base_file, head_untagged_file)
    assert result.base_path == base_file
    assert result.head_path == head_untagged_file


def test_pipeline_raises_for_missing_file(tmp_path):
    """run_tag_coverage_pipeline should raise an error for a non-existent file."""
    missing = str(tmp_path / "does_not_exist.json")
    with pytest.raises((FileNotFoundError, OSError)):
        run_tag_coverage_pipeline(missing, missing)
