"""Tests for apidiff.sorter module."""

import pytest
from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.sorter import sort_by_path, sort_by_severity, sort_changes


@pytest.fixture
def mixed_result():
    return DiffResult(
        changes=[
            Change(
                change_type=ChangeType.NON_BREAKING,
                path="/zebra.get.summary",
                description="Summary added",
            ),
            Change(
                change_type=ChangeType.BREAKING,
                path="/alpha.post.parameters",
                description="Param removed",
            ),
            Change(
                change_type=ChangeType.NON_BREAKING,
                path="/beta.delete.description",
                description="Description changed",
            ),
            Change(
                change_type=ChangeType.BREAKING,
                path="/alpha.get.responses",
                description="Response removed",
            ),
        ]
    )


def test_sort_by_path_ascending(mixed_result):
    result = sort_by_path(mixed_result)
    paths = [c.path for c in result.changes]
    assert paths == sorted(paths)


def test_sort_by_path_descending(mixed_result):
    result = sort_by_path(mixed_result, reverse=True)
    paths = [c.path for c in result.changes]
    assert paths == sorted(paths, reverse=True)


def test_sort_by_severity_breaking_first(mixed_result):
    result = sort_by_severity(mixed_result)
    types = [c.change_type for c in result.changes]
    breaking_indices = [i for i, t in enumerate(types) if t == ChangeType.BREAKING]
    non_breaking_indices = [
        i for i, t in enumerate(types) if t == ChangeType.NON_BREAKING
    ]
    assert max(breaking_indices) < min(non_breaking_indices)


def test_sort_changes_by_severity(mixed_result):
    result = sort_changes(mixed_result, by="severity")
    assert result.changes[0].change_type == ChangeType.BREAKING


def test_sort_changes_by_path(mixed_result):
    result = sort_changes(mixed_result, by="path")
    paths = [c.path for c in result.changes]
    assert paths == sorted(paths)


def test_sort_changes_by_path_reverse(mixed_result):
    result = sort_changes(mixed_result, by="path", reverse=True)
    paths = [c.path for c in result.changes]
    assert paths == sorted(paths, reverse=True)


def test_sort_changes_invalid_key(mixed_result):
    with pytest.raises(ValueError, match="Unknown sort key"):
        sort_changes(mixed_result, by="unknown")


def test_sort_does_not_mutate_original(mixed_result):
    original_paths = [c.path for c in mixed_result.changes]
    sort_by_path(mixed_result)
    assert [c.path for c in mixed_result.changes] == original_paths
