"""Tests for apidiff.scorer module."""
import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.scorer import ScoreResult, score_change, score_result


@pytest.fixture
def empty_result():
    return DiffResult(changes=[])


@pytest.fixture
def breaking_result():
    return DiffResult(changes=[
        Change(change_type=ChangeType.ENDPOINT_REMOVED, path="/users", method=None, description="removed"),
        Change(change_type=ChangeType.OPERATION_REMOVED, path="/items", method="delete", description="removed"),
    ])


@pytest.fixture
def mixed_result():
    return DiffResult(changes=[
        Change(change_type=ChangeType.ENDPOINT_REMOVED, path="/users", method=None, description="removed"),
        Change(change_type=ChangeType.ENDPOINT_ADDED, path="/products", method=None, description="added"),
    ])


def test_score_change_endpoint_removed():
    assert score_change(ChangeType.ENDPOINT_REMOVED) == 100


def test_score_change_endpoint_added():
    assert score_change(ChangeType.ENDPOINT_ADDED) == 5


def test_score_change_operation_removed():
    assert score_change(ChangeType.OPERATION_REMOVED) == 90


def test_score_result_empty(empty_result):
    sr = score_result(empty_result)
    assert sr.total == 0
    assert sr.breaking_score == 0
    assert sr.non_breaking_score == 0
    assert sr.change_count == 0
    assert sr.breaking_count == 0


def test_score_result_breaking(breaking_result):
    sr = score_result(breaking_result)
    assert sr.total == 190
    assert sr.breaking_score == 190
    assert sr.non_breaking_score == 0
    assert sr.breaking_count == 2


def test_score_result_mixed(mixed_result):
    sr = score_result(mixed_result)
    assert sr.breaking_score == 100
    assert sr.non_breaking_score == 5
    assert sr.total == 105
    assert sr.breaking_count == 1


def test_risk_level_none(empty_result):
    assert score_result(empty_result).risk_level == "none"


def test_risk_level_low():
    result = DiffResult(changes=[
        Change(change_type=ChangeType.ENDPOINT_ADDED, path="/x", method=None, description="added"),
    ])
    assert score_result(result).risk_level == "low"


def test_risk_level_medium(mixed_result):
    assert score_result(mixed_result).risk_level == "high"


def test_risk_level_high(breaking_result):
    assert score_result(breaking_result).risk_level == "high"


def test_score_result_returns_score_result_type(breaking_result):
    sr = score_result(breaking_result)
    assert isinstance(sr, ScoreResult)
