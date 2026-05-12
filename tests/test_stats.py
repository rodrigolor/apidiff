"""Tests for apidiff.stats."""
import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.stats import DiffStats, compute_stats, format_stats_text


@pytest.fixture()
def empty_result() -> DiffResult:
    return DiffResult(changes=[])


@pytest.fixture()
def mixed_result() -> DiffResult:
    return DiffResult(
        changes=[
            Change(change_type=ChangeType.BREAKING, path="/users", method="get", description="endpoint removed"),
            Change(change_type=ChangeType.BREAKING, path="/users", method="post", description="request body changed"),
            Change(change_type=ChangeType.NON_BREAKING, path="/items", method="get", description="description updated"),
        ]
    )


def test_compute_stats_empty(empty_result):
    stats = compute_stats(empty_result)
    assert stats.total == 0
    assert stats.breaking == 0
    assert stats.non_breaking == 0
    assert stats.breaking_ratio == 0.0
    assert stats.affected_paths == []


def test_compute_stats_totals(mixed_result):
    stats = compute_stats(mixed_result)
    assert stats.total == 3
    assert stats.breaking == 2
    assert stats.non_breaking == 1


def test_compute_stats_breaking_ratio(mixed_result):
    stats = compute_stats(mixed_result)
    assert abs(stats.breaking_ratio - 2 / 3) < 1e-9


def test_compute_stats_by_method(mixed_result):
    stats = compute_stats(mixed_result)
    assert stats.by_method["GET"] == 2
    assert stats.by_method["POST"] == 1


def test_compute_stats_by_path(mixed_result):
    stats = compute_stats(mixed_result)
    assert stats.by_path["/users"] == 2
    assert stats.by_path["/items"] == 1


def test_compute_stats_affected_paths(mixed_result):
    stats = compute_stats(mixed_result)
    assert "/items" in stats.affected_paths
    assert "/users" in stats.affected_paths
    assert stats.affected_paths == sorted(stats.affected_paths)


def test_format_stats_text_contains_totals(mixed_result):
    stats = compute_stats(mixed_result)
    text = format_stats_text(stats)
    assert "Total changes" in text
    assert "3" in text
    assert "Breaking" in text


def test_format_stats_text_ratio(mixed_result):
    stats = compute_stats(mixed_result)
    text = format_stats_text(stats)
    assert "%" in text


def test_format_stats_text_empty(empty_result):
    stats = compute_stats(empty_result)
    text = format_stats_text(stats)
    assert "0" in text
