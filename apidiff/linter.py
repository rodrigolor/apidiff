"""Linter for OpenAPI spec quality checks beyond diff comparisons."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LintIssue:
    code: str
    message: str
    path: Optional[str] = None
    severity: str = "warning"  # "error" or "warning"

    def __str__(self) -> str:
        location = f" [{self.path}]" if self.path else ""
        return f"[{self.severity.upper()}] {self.code}{location}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def __len__(self) -> int:
        return len(self.issues)


def _check_missing_descriptions(spec: dict) -> List[LintIssue]:
    issues = []
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete", "head", "options"):
                continue
            if not operation.get("description") and not operation.get("summary"):
                issues.append(LintIssue(
                    code="MISSING_DESCRIPTION",
                    message="Operation has no description or summary",
                    path=f"{method.upper()} {path}",
                    severity="warning",
                ))
    return issues


def _check_missing_response_codes(spec: dict) -> List[LintIssue]:
    issues = []
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            responses = operation.get("responses", {})
            if not responses:
                issues.append(LintIssue(
                    code="MISSING_RESPONSES",
                    message="Operation defines no responses",
                    path=f"{method.upper()} {path}",
                    severity="error",
                ))
            elif "200" not in responses and "201" not in responses and "default" not in responses:
                issues.append(LintIssue(
                    code="NO_SUCCESS_RESPONSE",
                    message="Operation has no 2xx or default response defined",
                    path=f"{method.upper()} {path}",
                    severity="warning",
                ))
    return issues


def _check_missing_operation_ids(spec: dict) -> List[LintIssue]:
    issues = []
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete", "head", "options"):
                continue
            if not operation.get("operationId"):
                issues.append(LintIssue(
                    code="MISSING_OPERATION_ID",
                    message="Operation is missing an operationId",
                    path=f"{method.upper()} {path}",
                    severity="warning",
                ))
    return issues


def lint_spec(spec: dict) -> LintResult:
    """Run all lint checks on a spec and return a LintResult."""
    issues: List[LintIssue] = []
    issues.extend(_check_missing_descriptions(spec))
    issues.extend(_check_missing_response_codes(spec))
    issues.extend(_check_missing_operation_ids(spec))
    return LintResult(issues=issues)
