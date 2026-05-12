"""Validate OpenAPI spec diffs for common rule violations."""

from dataclasses import dataclass, field
from typing import List

from apidiff.differ import DiffResult, ChangeType


@dataclass
class ValidationIssue:
    rule: str
    message: str
    path: str = ""
    method: str = ""

    def __str__(self) -> str:
        location = ""
        if self.path:
            location = f" [{self.method.upper()} {self.path}]" if self.method else f" [{self.path}]"
        return f"[{self.rule}]{location} {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0

    def __len__(self) -> int:
        return len(self.issues)


def validate_no_breaking_changes(result: DiffResult) -> ValidationResult:
    """Fail if any breaking changes are present."""
    issues = []
    for change in result.changes:
        if change.change_type == ChangeType.BREAKING:
            issues.append(ValidationIssue(
                rule="no-breaking-changes",
                message=change.description,
                path=change.path,
                method=change.method or "",
            ))
    return ValidationResult(issues=issues)


def validate_no_removed_endpoints(result: DiffResult) -> ValidationResult:
    """Fail if any endpoints have been removed."""
    issues = []
    for change in result.changes:
        if "removed" in change.description.lower() and change.path:
            issues.append(ValidationIssue(
                rule="no-removed-endpoints",
                message=change.description,
                path=change.path,
                method=change.method or "",
            ))
    return ValidationResult(issues=issues)


def run_validations(result: DiffResult, rules: List[str]) -> ValidationResult:
    """Run a named set of validation rules against a DiffResult."""
    rule_map = {
        "no-breaking-changes": validate_no_breaking_changes,
        "no-removed-endpoints": validate_no_removed_endpoints,
    }
    all_issues: List[ValidationIssue] = []
    for rule in rules:
        fn = rule_map.get(rule)
        if fn is None:
            raise ValueError(f"Unknown validation rule: {rule!r}")
        all_issues.extend(fn(result).issues)
    return ValidationResult(issues=all_issues)
