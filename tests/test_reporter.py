"""Tests for apidiff.reporter module."""
import pytest

from apidiff.differ import ChangeType, Change, DiffResult
from apidiff.reporter import summarize, format_summary_text, DiffSummary


@pytest.fixture
def empty_result():
    return DiffResult(changes=[])


@pytest.fixture
def mixed_result():
    return DiffResult(
        changes=[
            Change(
                change_type=ChangeType.ENDPOINT_REMOVED,
                path="/users",
                method="GET",
                description="Endpoint removed",
                breaking=True,
            ),
            Change(
                change_type=ChangeType.ENDPOINT_ADDED,
                path="/orders",
                method="POST",
                description="Endpoint added",
                breaking=False,
            ),
            Change(
                change_type=ChangeType.ENDPOINT_REMOVED,
                path="/items",
                method="DELETE",
                description="Endpoint removed",
                breaking=True,
            ),
        ]
    )


def test_summarize_empty(empty_result):
    summary = summarize(empty_result)
    assert summary.total == 0
    assert summary.breaking == 0
    assert summary.non_breaking == 0
    assert summary.by_type == {}
    assert not summary.has_breaking
    assert not summary.has_changes


def test_summarize_counts(mixed_result):
    summary = summarize(mixed_result)
    assert summary.total == 3
    assert summary.breaking == 2
    assert summary.non_breaking == 1
    assert summary.has_breaking
    assert summary.has_changes


def test_summarize_by_type(mixed_result):
    summary = summarize(mixed_result)
    assert summary.by_type[ChangeType.ENDPOINT_REMOVED.value] == 2
    assert summary.by_type[ChangeType.ENDPOINT_ADDED.value] == 1


def test_format_summary_text_empty(empty_result):
    summary = summarize(empty_result)
    text = format_summary_text(summary)
    assert "Diff Summary" in text
    assert "Total changes  : 0" in text
    assert "Breaking       : 0" in text
    assert "Non-breaking   : 0" in text


def test_format_summary_text_mixed(mixed_result):
    summary = summarize(mixed_result)
    text = format_summary_text(summary)
    assert "Total changes  : 3" in text
    assert "Breaking       : 2" in text
    assert "Non-breaking   : 1" in text
    assert "By change type" in text
    assert ChangeType.ENDPOINT_REMOVED.value in text
    assert ChangeType.ENDPOINT_ADDED.value in text


def test_format_summary_no_by_type_section_when_empty(empty_result):
    summary = summarize(empty_result)
    text = format_summary_text(summary)
    assert "By change type" not in text
