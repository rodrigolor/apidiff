"""Endpoint-level comparator: compare two specs and produce a structured comparison report."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from apidiff.differ import DiffResult, Change, ChangeType


@dataclass
class EndpointComparison:
    """Comparison result for a single endpoint (path + method)."""

    path: str
    method: Optional[str]
    changes: List[Change] = field(default_factory=list)

    @property
    def has_breaking(self) -> bool:
        return any(c.change_type == ChangeType.BREAKING for c in self.changes)

    @property
    def has_non_breaking(self) -> bool:
        return any(c.change_type == ChangeType.NON_BREAKING for c in self.changes)


@dataclass
class ComparisonReport:
    """Full comparison report grouping changes by endpoint."""

    endpoints: List[EndpointComparison] = field(default_factory=list)

    @property
    def breaking_endpoints(self) -> List[EndpointComparison]:
        return [e for e in self.endpoints if e.has_breaking]

    @property
    def total_changes(self) -> int:
        return sum(len(e.changes) for e in self.endpoints)

    @property
    def total_breaking(self) -> int:
        return sum(1 for e in self.endpoints if e.has_breaking)


def build_comparison_report(diff_result: DiffResult) -> ComparisonReport:
    """Group changes from a DiffResult into per-endpoint comparisons."""
    grouped: Dict[tuple, List[Change]] = {}

    for change in diff_result.changes:
        key = (change.path, change.method)
        grouped.setdefault(key, []).append(change)

    endpoints = [
        EndpointComparison(path=path, method=method, changes=changes)
        for (path, method), changes in sorted(grouped.items(), key=lambda x: (x[0][0] or "", x[0][1] or ""))
    ]

    return ComparisonReport(endpoints=endpoints)


def format_comparison_text(report: ComparisonReport) -> str:
    """Render a ComparisonReport as a human-readable text block."""
    if not report.endpoints:
        return "No changes detected."

    lines: List[str] = []
    for ep in report.endpoints:
        label = f"{ep.method.upper()} {ep.path}" if ep.method else ep.path
        lines.append(f"  {label}")
        for change in ep.changes:
            tag = "[BREAKING]" if change.change_type == ChangeType.BREAKING else "[non-breaking]"
            lines.append(f"    {tag} {change.description}")
    return "\n".join(lines)
