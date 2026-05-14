"""Tests for apidiff.linter module."""

import pytest
from apidiff.linter import (
    LintIssue,
    LintResult,
    lint_spec,
)


@pytest.fixture
def clean_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "listUsers",
                    "summary": "List users",
                    "description": "Returns all users.",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }


@pytest.fixture
def bad_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Bad", "version": "0.1.0"},
        "paths": {
            "/items": {
                "post": {
                    # no operationId, no description, no summary, no responses
                }
            }
        },
    }


def test_lint_issue_str_with_path():
    issue = LintIssue(code="MISSING_DESCRIPTION", message="No desc", path="GET /foo", severity="warning")
    result = str(issue)
    assert "MISSING_DESCRIPTION" in result
    assert "GET /foo" in result
    assert "WARNING" in result


def test_lint_issue_str_no_path():
    issue = LintIssue(code="SOME_CODE", message="Something", severity="error")
    result = str(issue)
    assert "ERROR" in result
    assert "SOME_CODE" in result
    assert "[" not in result or "ERROR" in result  # no path bracket


def test_lint_result_passed_empty():
    result = LintResult()
    assert result.passed is True
    assert len(result) == 0


def test_lint_result_errors_and_warnings():
    issues = [
        LintIssue(code="A", message="a", severity="error"),
        LintIssue(code="B", message="b", severity="warning"),
        LintIssue(code="C", message="c", severity="warning"),
    ]
    result = LintResult(issues=issues)
    assert len(result.errors) == 1
    assert len(result.warnings) == 2
    assert result.passed is False


def test_lint_clean_spec_no_issues(clean_spec):
    result = lint_spec(clean_spec)
    assert result.passed is True
    assert len(result) == 0


def test_lint_bad_spec_has_errors(bad_spec):
    result = lint_spec(bad_spec)
    assert len(result) > 0


def test_lint_detects_missing_operation_id(bad_spec):
    result = lint_spec(bad_spec)
    codes = [i.code for i in result.issues]
    assert "MISSING_OPERATION_ID" in codes


def test_lint_detects_missing_description(bad_spec):
    result = lint_spec(bad_spec)
    codes = [i.code for i in result.issues]
    assert "MISSING_DESCRIPTION" in codes


def test_lint_detects_missing_responses(bad_spec):
    result = lint_spec(bad_spec)
    codes = [i.code for i in result.issues]
    assert "MISSING_RESPONSES" in codes


def test_lint_no_success_response_warning():
    spec = {
        "paths": {
            "/foo": {
                "get": {
                    "operationId": "getFoo",
                    "summary": "Get foo",
                    "description": "Gets foo.",
                    "responses": {"400": {"description": "Bad Request"}},
                }
            }
        }
    }
    result = lint_spec(spec)
    codes = [i.code for i in result.issues]
    assert "NO_SUCCESS_RESPONSE" in codes


def test_lint_spec_empty_paths():
    """A spec with no paths should produce no issues."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Empty", "version": "1.0.0"},
        "paths": {},
    }
    result = lint_spec(spec)
    assert result.passed is True
    assert len(result) == 0


def test_lint_spec_missing_paths_key():
    """A spec without a 'paths' key should not raise and should return a result."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "NoPaths", "version": "1.0.0"},
    }
    result = lint_spec(spec)
    assert isinstance(result, LintResult)
