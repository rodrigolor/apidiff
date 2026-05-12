"""Additional formatting tests for comparator output."""

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.comparator import build_comparison_report, format_comparison_text


@pytest.fixture
def single_breaking():
    return DiffResult(
        changes=[
            Change(
                change_type=ChangeType.BREAKING,
                path="/items",
                method="delete",
                description="Endpoint removed",
            )
        ]
    )


@pytest.fixture
def multi_change_same_endpoint():
    return DiffResult(
        changes=[
            Change(change_type=ChangeType.BREAKING, path="/items", method="post", description="Required field added"),
            Change(change_type=ChangeType.NON_BREAKING, path="/items", method="post", description="New optional field"),
        ]
    )


def test_format_single_breaking_contains_method(single_breaking):
    report = build_comparison_report(single_breaking)
    text = format_comparison_text(report)
    assert "DELETE" in text


def test_format_single_breaking_contains_description(single_breaking):
    report = build_comparison_report(single_breaking)
    text = format_comparison_text(report)
    assert "Endpoint removed" in text


def test_format_multi_change_same_endpoint_groups(multi_change_same_endpoint):
    report = build_comparison_report(multi_change_same_endpoint)
    assert len(report.endpoints) == 1
    assert len(report.endpoints[0].changes) == 2


def test_format_multi_change_both_labels(multi_change_same_endpoint):
    report = build_comparison_report(multi_change_same_endpoint)
    text = format_comparison_text(report)
    assert "[BREAKING]" in text
    assert "[non-breaking]" in text


def test_format_no_method_shows_path_only():
    result = DiffResult(
        changes=[
            Change(change_type=ChangeType.NON_BREAKING, path="/info", method=None, description="Title changed")
        ]
    )
    report = build_comparison_report(result)
    text = format_comparison_text(report)
    assert "/info" in text
    assert "None" not in text
