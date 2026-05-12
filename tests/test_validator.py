"""Tests for apidiff.validator module."""

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.validator import (
    ValidationIssue,
    ValidationResult,
    validate_no_breaking_changes,
    validate_no_removed_endpoints,
    run_validations,
)


@pytest.fixture
def empty_result():
    return DiffResult(changes=[])


@pytest.fixture
def mixed_result():
    return DiffResult(changes=[
        Change(
            change_type=ChangeType.BREAKING,
            description="Endpoint removed: DELETE /users",
            path="/users",
            method="delete",
        ),
        Change(
            change_type=ChangeType.NON_BREAKING,
            description="Endpoint added: GET /health",
            path="/health",
            method="get",
        ),
    ])


def test_validation_issue_str_with_method():
    issue = ValidationIssue(rule="no-breaking-changes", message="Removed", path="/x", method="get")
    assert "[no-breaking-changes]" in str(issue)
    assert "[GET /x]" in str(issue)
    assert "Removed" in str(issue)


def test_validation_issue_str_path_only():
    issue = ValidationIssue(rule="some-rule", message="msg", path="/x")
    assert "[/x]" in str(issue)


def test_validation_issue_str_no_location():
    issue = ValidationIssue(rule="some-rule", message="msg")
    assert "[some-rule] msg" == str(issue)


def test_validation_result_passed_when_empty():
    vr = ValidationResult(issues=[])
    assert vr.passed is True
    assert len(vr) == 0


def test_validation_result_failed_when_issues():
    vr = ValidationResult(issues=[ValidationIssue(rule="r", message="m")])
    assert vr.passed is False
    assert len(vr) == 1


def test_validate_no_breaking_changes_passes(empty_result):
    vr = validate_no_breaking_changes(empty_result)
    assert vr.passed


def test_validate_no_breaking_changes_fails(mixed_result):
    vr = validate_no_breaking_changes(mixed_result)
    assert not vr.passed
    assert len(vr) == 1
    assert vr.issues[0].rule == "no-breaking-changes"


def test_validate_no_removed_endpoints_fails(mixed_result):
    vr = validate_no_removed_endpoints(mixed_result)
    assert not vr.passed
    assert any("removed" in i.message.lower() for i in vr.issues)


def test_run_validations_combines_rules(mixed_result):
    vr = run_validations(mixed_result, ["no-breaking-changes", "no-removed-endpoints"])
    assert not vr.passed


def test_run_validations_empty_rules(mixed_result):
    vr = run_validations(mixed_result, [])
    assert vr.passed


def test_run_validations_unknown_rule(mixed_result):
    with pytest.raises(ValueError, match="Unknown validation rule"):
        run_validations(mixed_result, ["nonexistent-rule"])
