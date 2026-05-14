"""Tests for apidiff.tag_coverage."""
import pytest

from apidiff.tag_coverage import (
    TagCoverageResult,
    compute_tag_coverage,
    format_tag_coverage_text,
)


@pytest.fixture()
def fully_tagged_spec():
    return {
        "openapi": "3.0.0",
        "paths": {
            "/pets": {
                "get": {"tags": ["pets"], "responses": {"200": {"description": "ok"}}},
                "post": {"tags": ["pets"], "responses": {"201": {"description": "created"}}},
            },
            "/users": {
                "get": {"tags": ["users"], "responses": {"200": {"description": "ok"}}},
            },
        },
    }


@pytest.fixture()
def partially_tagged_spec():
    return {
        "openapi": "3.0.0",
        "paths": {
            "/pets": {
                "get": {"tags": ["pets"], "responses": {"200": {"description": "ok"}}},
                "post": {"responses": {"201": {"description": "created"}}},
            },
        },
    }


def test_compute_tag_coverage_empty_spec():
    result = compute_tag_coverage({})
    assert result.total_operations == 0
    assert result.tagged_operations == 0
    assert result.coverage_ratio == 1.0
    assert result.is_fully_tagged is False


def test_compute_tag_coverage_fully_tagged(fully_tagged_spec):
    result = compute_tag_coverage(fully_tagged_spec)
    assert result.total_operations == 3
    assert result.tagged_operations == 3
    assert result.coverage_percent == 100.0
    assert result.is_fully_tagged is True
    assert result.untagged_paths == []


def test_compute_tag_coverage_partial(partially_tagged_spec):
    result = compute_tag_coverage(partially_tagged_spec)
    assert result.total_operations == 2
    assert result.tagged_operations == 1
    assert result.coverage_percent == 50.0
    assert result.is_fully_tagged is False
    assert "/pets" in result.untagged_paths


def test_tag_counts_aggregated(fully_tagged_spec):
    result = compute_tag_coverage(fully_tagged_spec)
    assert result.tag_counts["pets"] == 2
    assert result.tag_counts["users"] == 1


def test_non_http_keys_ignored():
    spec = {
        "paths": {
            "/items": {
                "get": {"tags": ["items"], "responses": {}},
                "summary": "Item endpoints",
                "parameters": [],
            }
        }
    }
    result = compute_tag_coverage(spec)
    assert result.total_operations == 1


def test_format_tag_coverage_text_includes_percent(fully_tagged_spec):
    result = compute_tag_coverage(fully_tagged_spec)
    text = format_tag_coverage_text(result)
    assert "100.0%" in text


def test_format_tag_coverage_text_lists_untagged(partially_tagged_spec):
    result = compute_tag_coverage(partially_tagged_spec)
    text = format_tag_coverage_text(result)
    assert "/pets" in text
    assert "Untagged paths" in text


def test_format_tag_coverage_text_tag_usage(fully_tagged_spec):
    result = compute_tag_coverage(fully_tagged_spec)
    text = format_tag_coverage_text(result)
    assert "pets: 2" in text
    assert "users: 1" in text
