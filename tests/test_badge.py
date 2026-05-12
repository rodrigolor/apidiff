"""Tests for apidiff.badge module."""
import pytest

from apidiff.scorer import ScoreResult
from apidiff.badge import BadgeData, make_badge


@pytest.fixture
def no_changes_score():
    return ScoreResult(total=0, breaking_score=0, non_breaking_score=0, change_count=0, breaking_count=0)


@pytest.fixture
def low_score():
    return ScoreResult(total=10, breaking_score=0, non_breaking_score=10, change_count=2, breaking_count=0)


@pytest.fixture
def high_score():
    return ScoreResult(total=200, breaking_score=190, non_breaking_score=10, change_count=4, breaking_count=3)


def test_badge_no_changes_message(no_changes_score):
    badge = make_badge(no_changes_score)
    assert badge.message == "no changes"


def test_badge_no_changes_color(no_changes_score):
    badge = make_badge(no_changes_score)
    assert badge.color == "brightgreen"


def test_badge_non_breaking_message(low_score):
    badge = make_badge(low_score)
    assert badge.message == "2 non-breaking"


def test_badge_non_breaking_color(low_score):
    badge = make_badge(low_score)
    assert badge.color == "green"


def test_badge_breaking_message(high_score):
    badge = make_badge(high_score)
    assert badge.message == "3 breaking"


def test_badge_breaking_color(high_score):
    badge = make_badge(high_score)
    assert badge.color == "red"


def test_badge_custom_label(no_changes_score):
    badge = make_badge(no_changes_score, label="openapi")
    assert badge.label == "openapi"


def test_badge_default_label(no_changes_score):
    badge = make_badge(no_changes_score)
    assert badge.label == "api-diff"


def test_badge_to_dict_keys(high_score):
    d = make_badge(high_score).to_dict()
    assert set(d.keys()) == {"schemaVersion", "label", "message", "color"}


def test_badge_to_dict_schema_version(high_score):
    d = make_badge(high_score).to_dict()
    assert d["schemaVersion"] == 1


def test_badge_returns_badge_data(no_changes_score):
    assert isinstance(make_badge(no_changes_score), BadgeData)
