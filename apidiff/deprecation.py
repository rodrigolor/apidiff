"""Detect and report deprecated endpoints and fields in an OpenAPI spec diff."""

from dataclasses import dataclass, field
from typing import List, Optional

from apidiff.differ import DiffResult, Change, ChangeType


@dataclass
class DeprecationWarning:
    path: str
    method: Optional[str]
    description: str

    def __str__(self) -> str:
        loc = f"{self.method.upper()} {self.path}" if self.method else self.path
        return f"[DEPRECATED] {loc}: {self.description}"


@dataclass
class DeprecationReport:
    warnings: List[DeprecationWarning] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.warnings)

    @property
    def has_deprecations(self) -> bool:
        return self.count > 0


def _is_deprecation_change(change: Change) -> bool:
    """Return True if the change represents a newly deprecated item."""
    description = change.description.lower()
    return "deprecated" in description


def scan_deprecations(result: DiffResult) -> DeprecationReport:
    """Scan a DiffResult and collect all deprecation-related changes."""
    report = DeprecationReport()
    for change in result.changes:
        if _is_deprecation_change(change):
            warning = DeprecationWarning(
                path=change.path,
                method=change.method,
                description=change.description,
            )
            report.warnings.append(warning)
    return report


def scan_spec_deprecations(spec: dict) -> DeprecationReport:
    """Scan a raw OpenAPI spec for already-deprecated endpoints."""
    report = DeprecationReport()
    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}:
                continue
            if isinstance(operation, dict) and operation.get("deprecated", False):
                warning = DeprecationWarning(
                    path=path,
                    method=method,
                    description="Operation is marked as deprecated in spec.",
                )
                report.warnings.append(warning)
    return report


def format_deprecation_report(report: DeprecationReport) -> str:
    """Format a DeprecationReport as a human-readable string."""
    if not report.has_deprecations:
        return "No deprecations found."
    lines = [f"Deprecations ({report.count}):"] + [f"  {w}" for w in report.warnings]
    return "\n".join(lines)
