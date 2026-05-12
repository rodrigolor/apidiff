"""Tests for apidiff.comparator."""

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.comparator import (
    EndpointComparison,
    ComparisonReport,
    build_comparison_report,
    format_comparison_text,
)


@pytest.fixture
def empty_result():
    return DiffResult(changes=[])


@pytest.fixture
def mixed_result():
    return DiffResult(
        changes=[
            Change(change_type=ChangeType.BREAKING, path="/users", method="delete", description="Endpoint removed"),
            Change(change_type=ChangeType.NON_BREAKING, path="/users", method="get", description="Description updated"),
            Change(change_type=ChangeType.BREAKING, path="/orders", method="post", description="Required field added"),
        ]
    )


def test_build_comparison_report_empty(empty_result):
    report = build_comparison_report(empty_result)
    assert report.endpoints == []
    assert report.total_changes == 0
    assert report.total_breaking == 0


def test_build_comparison_report_groups_by_endpoint(mixed_result):
    report = build_comparison_report(mixed_result)
    paths = [(e.path, e.method) for e in report.endpoints]
    assert ("/orders", "post") in paths
    assert ("/users", "delete") in paths
    assert ("/users", "get") in paths


def test_build_comparison_report_total_changes(mixed_result):
    report = build_comparison_report(mixed_result)
    assert report.total_changes == 3


def test_build_comparison_report_breaking_endpoints(mixed_result):
    report = build_comparison_report(mixed_result)
    breaking = report.breaking_endpoints
    breaking_keys = [(e.path, e.method) for e in breaking]
    assert ("/users", "delete") in breaking_keys
    assert ("/orders", "post") in breaking_keys
    assert ("/users", "get") not in breaking_keys


def test_endpoint_comparison_has_breaking():
    ep = EndpointComparison(
        path="/x",
        method="delete",
        changes=[Change(change_type=ChangeType.BREAKING, path="/x", method="delete", description="removed")],
    )
    assert ep.has_breaking is True
    assert ep.has_non_breaking is False


def test_endpoint_comparison_has_non_breaking():
    ep = EndpointComparison(
        path="/x",
        method="get",
        changes=[Change(change_type=ChangeType.NON_BREAKING, path="/x", method="get", description="desc")],
    )
    assert ep.has_breaking is False
    assert ep.has_non_breaking is True


def test_format_comparison_text_empty(empty_result):
    report = build_comparison_report(empty_result)
    text = format_comparison_text(report)
    assert text == "No changes detected."


def test_format_comparison_text_contains_path(mixed_result):
    report = build_comparison_report(mixed_result)
    text = format_comparison_text(report)
    assert "/users" in text
    assert "/orders" in text


def test_format_comparison_text_breaking_label(mixed_result):
    report = build_comparison_report(mixed_result)
    text = format_comparison_text(report)
    assert "[BREAKING]" in text


def test_format_comparison_text_non_breaking_label(mixed_result):
    report = build_comparison_report(mixed_result)
    text = format_comparison_text(report)
    assert "[non-breaking]" in text


def test_total_breaking_count(mixed_result):
    report = build_comparison_report(mixed_result)
    assert report.total_breaking == 2
