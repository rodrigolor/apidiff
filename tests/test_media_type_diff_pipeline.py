"""Tests for apidiff.media_type_diff_pipeline."""
import json
import os
import tempfile

import pytest

from apidiff.media_type_diff_pipeline import (
    MediaTypeDiffPipelineResult,
    run_media_type_diff_pipeline,
)


def _write(spec: dict) -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    )
    json.dump(spec, f)
    f.close()
    return f.name


BASE = {
    "openapi": "3.0.0",
    "info": {"title": "T", "version": "1"},
    "paths": {
        "/ping": {
            "get": {
                "responses": {
                    "200": {
                        "content": {"application/json": {}}
                    }
                }
            }
        }
    },
}

HEAD_REMOVED = {
    "openapi": "3.0.0",
    "info": {"title": "T", "version": "2"},
    "paths": {
        "/ping": {
            "get": {
                "responses": {"200": {}}
            }
        }
    },
}


@pytest.fixture
def base_file():
    path = _write(BASE)
    yield path
    os.unlink(path)


@pytest.fixture
def head_removed_file():
    path = _write(HEAD_REMOVED)
    yield path
    os.unlink(path)


@pytest.fixture
def head_identical_file():
    path = _write(BASE)
    yield path
    os.unlink(path)


def test_pipeline_returns_correct_type(base_file, head_identical_file):
    result = run_media_type_diff_pipeline(base_file, head_identical_file)
    assert isinstance(result, MediaTypeDiffPipelineResult)


def test_pipeline_no_changes_when_identical(base_file, head_identical_file):
    result = run_media_type_diff_pipeline(base_file, head_identical_file)
    assert not result.has_changes()
    assert not result.has_breaking()


def test_pipeline_detects_removal(base_file, head_removed_file):
    result = run_media_type_diff_pipeline(base_file, head_removed_file)
    assert result.has_changes()
    assert result.has_breaking()
    assert result.total() == 1


def test_pipeline_summary_no_changes(base_file, head_identical_file):
    result = run_media_type_diff_pipeline(base_file, head_identical_file)
    assert "No media type changes" in result.summary_text()


def test_pipeline_summary_with_breaking(base_file, head_removed_file):
    result = run_media_type_diff_pipeline(base_file, head_removed_file)
    text = result.summary_text()
    assert "breaking" in text
    assert "1" in text


def test_pipeline_stores_paths(base_file, head_removed_file):
    result = run_media_type_diff_pipeline(base_file, head_removed_file)
    assert result.base_path == base_file
    assert result.head_path == head_removed_file
