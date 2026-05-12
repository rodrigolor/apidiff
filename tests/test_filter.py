"""Tests for apidiff.filter module."""

import pytest
from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.filter import (
    filter_breaking,
    filter_non_breaking,
    filter_by_path,
    filter_by_method,
    apply_filters,
)


@pytest.fixture
def mixed_result():
    return DiffResult(
        changes=[
            Change(
                change_type=ChangeType.BREAKING,
                path="/pets.get.responses",
                description="Response removed",
            ),
            Change(
                change_type=ChangeType.NON_BREAKING,
                path="/pets.post.description",
                description="Description updated",
            ),
            Change(
                change_type=ChangeType.BREAKING,
                path="/users.delete.parameters",
                description="Required param removed",
            ),
            Change(
                change_type=ChangeType.NON_BREAKING,
                path="/users.get.summary",
                description="Summary added",
            ),
        ]
    )


def test_filter_breaking(mixed_result):
    result = filter_breaking(mixed_result)
    assert len(result.changes) == 2
    assert all(c.change_type == ChangeType.BREAKING for c in result.changes)


def test_filter_non_breaking(mixed_result):
    result = filter_non_breaking(mixed_result)
    assert len(result.changes) == 2
    assert all(c.change_type == ChangeType.NON_BREAKING for c in result.changes)


def test_filter_by_path(mixed_result):
    result = filter_by_path(mixed_result, "/users")
    assert len(result.changes) == 2
    assert all(c.path.startswith("/users") for c in result.changes)


def test_filter_by_path_no_match(mixed_result):
    result = filter_by_path(mixed_result, "/orders")
    assert len(result.changes) == 0


def test_filter_by_method(mixed_result):
    result = filter_by_method(mixed_result, "get")
    assert len(result.changes) == 2
    for c in result.changes:
        parts = c.path.split(".")
        assert parts[1].lower() == "get"


def test_filter_by_method_case_insensitive(mixed_result):
    result_lower = filter_by_method(mixed_result, "get")
    result_upper = filter_by_method(mixed_result, "GET")
    assert len(result_lower.changes) == len(result_upper.changes)


def test_apply_filters_breaking_only(mixed_result):
    result = apply_filters(mixed_result, breaking_only=True)
    assert len(result.changes) == 2
    assert all(c.change_type == ChangeType.BREAKING for c in result.changes)


def test_apply_filters_non_breaking_only(mixed_result):
    result = apply_filters(mixed_result, non_breaking_only=True)
    assert len(result.changes) == 2


def test_apply_filters_combined(mixed_result):
    result = apply_filters(mixed_result, breaking_only=True, path_prefix="/pets")
    assert len(result.changes) == 1
    assert result.changes[0].path == "/pets.get.responses"


def test_apply_filters_no_filters(mixed_result):
    result = apply_filters(mixed_result)
    assert len(result.changes) == 4
