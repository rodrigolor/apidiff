"""Tests for apidiff.deprecation module."""

import pytest

from apidiff.deprecation import (
    DeprecationWarning,
    DeprecationReport,
    scan_deprecations,
    scan_spec_deprecations,
    format_deprecation_report,
)
from apidiff.differ import Change, ChangeType, DiffResult


@pytest.fixture
def diff_result_with_deprecation():
    return DiffResult(
        changes=[
            Change(
                change_type=ChangeType.NON_BREAKING,
                path="/users",
                method="get",
                description="Operation marked as deprecated.",
            ),
            Change(
                change_type=ChangeType.BREAKING,
                path="/orders",
                method="post",
                description="Request body field removed.",
            ),
        ]
    )


@pytest.fixture
def spec_with_deprecated():
    return {
        "paths": {
            "/users": {
                "get": {"deprecated": True, "summary": "List users"},
                "post": {"summary": "Create user"},
            },
            "/orders": {
                "delete": {"deprecated": True, "summary": "Delete order"},
            },
        }
    }


def test_deprecation_warning_str_with_method():
    w = DeprecationWarning(path="/users", method="get", description="Deprecated.")
    assert "GET /users" in str(w)
    assert "[DEPRECATED]" in str(w)


def test_deprecation_warning_str_no_method():
    w = DeprecationWarning(path="/users", method=None, description="Deprecated.")
    assert "/users" in str(w)
    assert "GET" not in str(w)


def test_deprecation_report_empty():
    report = DeprecationReport()
    assert report.count == 0
    assert not report.has_deprecations


def test_scan_deprecations_finds_deprecated(diff_result_with_deprecation):
    report = scan_deprecations(diff_result_with_deprecation)
    assert report.has_deprecations
    assert report.count == 1
    assert report.warnings[0].path == "/users"


def test_scan_deprecations_ignores_non_deprecated(diff_result_with_deprecation):
    report = scan_deprecations(diff_result_with_deprecation)
    paths = [w.path for w in report.warnings]
    assert "/orders" not in paths


def test_scan_spec_deprecations(spec_with_deprecated):
    report = scan_spec_deprecations(spec_with_deprecated)
    assert report.count == 2
    paths = [w.path for w in report.warnings]
    assert "/users" in paths
    assert "/orders" in paths


def test_scan_spec_deprecations_skips_non_deprecated():
    spec = {"paths": {"/ping": {"get": {"summary": "Ping"}}}}
    report = scan_spec_deprecations(spec)
    assert not report.has_deprecations


def test_format_deprecation_report_empty():
    report = DeprecationReport()
    text = format_deprecation_report(report)
    assert "No deprecations" in text


def test_format_deprecation_report_with_warnings():
    report = DeprecationReport(
        warnings=[
            DeprecationWarning(path="/users", method="get", description="Deprecated."),
        ]
    )
    text = format_deprecation_report(report)
    assert "Deprecations (1)" in text
    assert "GET /users" in text
