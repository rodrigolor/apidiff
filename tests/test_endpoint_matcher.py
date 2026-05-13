"""Tests for apidiff.endpoint_matcher."""

import pytest

from apidiff.endpoint_matcher import (
    EndpointMatch,
    MatchReport,
    find_endpoint_matches,
    match_from_diff,
    _similarity,
)
from apidiff.differ import Change, ChangeType, DiffResult


# ---------------------------------------------------------------------------
# Unit tests for _similarity
# ---------------------------------------------------------------------------

def test_similarity_identical():
    assert _similarity("/users", "/users") == 1.0


def test_similarity_completely_different():
    score = _similarity("/users", "/xyz")
    assert score < 0.5


def test_similarity_partial():
    score = _similarity("/users/{id}", "/users/{user_id}")
    assert 0.5 < score < 1.0


# ---------------------------------------------------------------------------
# find_endpoint_matches
# ---------------------------------------------------------------------------

def test_exact_match_found():
    report = find_endpoint_matches(["/users"], ["/users"])
    assert report.total_matches == 1
    assert report.matches[0].old_path == "/users"
    assert report.matches[0].new_path == "/users"
    assert report.matches[0].score == pytest.approx(1.0)


def test_fuzzy_match_above_threshold():
    report = find_endpoint_matches(["/users/{id}"], ["/users/{user_id}"], threshold=0.6)
    assert report.total_matches == 1
    assert report.unmatched_old == []
    assert report.unmatched_new == []


def test_no_match_below_threshold():
    report = find_endpoint_matches(["/users"], ["/orders"], threshold=0.9)
    assert report.total_matches == 0
    assert "/users" in report.unmatched_old
    assert "/orders" in report.unmatched_new


def test_unmatched_new_paths_captured():
    report = find_endpoint_matches([], ["/new-endpoint"])
    assert report.unmatched_new == ["/new-endpoint"]
    assert report.total_matches == 0


def test_each_new_path_matched_at_most_once():
    # Two old paths both close to the same new path — only one should match.
    report = find_endpoint_matches(
        ["/items/{id}", "/items/{item_id}"],
        ["/items/{item_id}"],
        threshold=0.7,
    )
    assert report.total_matches == 1
    # The unmatched old should contain exactly one entry.
    assert len(report.unmatched_old) == 1


def test_has_matches_false_when_empty():
    report = MatchReport()
    assert not report.has_matches


def test_has_matches_true():
    report = MatchReport(matches=[EndpointMatch("/a", "/b", 0.8)])
    assert report.has_matches


# ---------------------------------------------------------------------------
# match_from_diff
# ---------------------------------------------------------------------------

def _make_change(change_type: ChangeType, path: str) -> Change:
    return Change(change_type=change_type, path=path, method=None, description="test")


@pytest.fixture
def diff_with_rename():
    changes = [
        _make_change(ChangeType.ENDPOINT_REMOVED, "/users/{id}"),
        _make_change(ChangeType.ENDPOINT_ADDED, "/users/{user_id}"),
    ]
    return DiffResult(changes=changes)


def test_match_from_diff_finds_rename(diff_with_rename):
    report = match_from_diff(diff_with_rename, threshold=0.6)
    assert report.total_matches == 1
    assert report.matches[0].old_path == "/users/{id}"
    assert report.matches[0].new_path == "/users/{user_id}"


def test_match_from_diff_empty_diff():
    empty = DiffResult(changes=[])
    report = match_from_diff(empty)
    assert report.total_matches == 0
    assert report.unmatched_old == []
    assert report.unmatched_new == []


def test_endpoint_match_str():
    m = EndpointMatch("/old", "/new", 0.75)
    assert "->" in str(m)
    assert "0.75" in str(m)
