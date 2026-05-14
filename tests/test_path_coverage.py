"""Tests for apidiff.path_coverage."""

import pytest
from apidiff.differ import DiffResult, Change, ChangeType
from apidiff.path_coverage import (
    CoverageResult,
    _collect_spec_paths,
    compute_path_coverage,
    format_coverage_text,
)


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/users": {"get": {"responses": {"200": {"description": "ok"}}}},
            "/items": {"get": {"responses": {"200": {"description": "ok"}}}},
        },
    }


@pytest.fixture
def head_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "2.0"},
        "paths": {
            "/users": {"get": {"responses": {"200": {"description": "ok"}}}},
            "/orders": {"post": {"responses": {"201": {"description": "created"}}}},
        },
    }


@pytest.fixture
def empty_diff():
    return DiffResult(changes=[])


@pytest.fixture
def mixed_diff():
    return DiffResult(
        changes=[
            Change(change_type=ChangeType.ENDPOINT_REMOVED, path="/items", method="get", description="removed"),
            Change(change_type=ChangeType.ENDPOINT_ADDED, path="/orders", method="post", description="added"),
            Change(change_type=ChangeType.RESPONSE_ADDED, path="/users", method="get", description="response added"),
        ]
    )


def test_collect_spec_paths_returns_keys(base_spec):
    paths = _collect_spec_paths(base_spec)
    assert "/users" in paths
    assert "/items" in paths


def test_collect_spec_paths_empty_spec():
    assert _collect_spec_paths({}) == set()


def test_coverage_ratio_zero_when_no_paths():
    result = CoverageResult(total_paths=0, changed_paths=0)
    assert result.coverage_ratio == 0.0


def test_coverage_ratio_partial():
    result = CoverageResult(total_paths=4, changed_paths=2)
    assert result.coverage_ratio == 0.5
    assert result.coverage_percent == 50.0


def test_compute_coverage_empty_diff(base_spec, head_spec, empty_diff):
    coverage = compute_path_coverage(base_spec, head_spec, empty_diff)
    assert coverage.changed_paths == 0
    assert coverage.total_paths == 3  # /users, /items, /orders


def test_compute_coverage_counts_added(base_spec, head_spec, mixed_diff):
    coverage = compute_path_coverage(base_spec, head_spec, mixed_diff)
    assert "/orders" in coverage.added_paths


def test_compute_coverage_counts_removed(base_spec, head_spec, mixed_diff):
    coverage = compute_path_coverage(base_spec, head_spec, mixed_diff)
    assert "/items" in coverage.removed_paths


def test_compute_coverage_counts_modified(base_spec, head_spec, mixed_diff):
    coverage = compute_path_coverage(base_spec, head_spec, mixed_diff)
    assert "/users" in coverage.modified_paths


def test_compute_coverage_changed_paths(base_spec, head_spec, mixed_diff):
    coverage = compute_path_coverage(base_spec, head_spec, mixed_diff)
    assert coverage.changed_paths == 3


def test_format_coverage_text_contains_percent(base_spec, head_spec, mixed_diff):
    coverage = compute_path_coverage(base_spec, head_spec, mixed_diff)
    text = format_coverage_text(coverage)
    assert "%" in text
    assert "Added" in text
    assert "Removed" in text
    assert "Modified" in text
