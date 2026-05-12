"""Summary reporter for diff results."""
from dataclasses import dataclass
from typing import Dict

from apidiff.differ import DiffResult, ChangeType


@dataclass
class DiffSummary:
    """Aggregated statistics about a diff result."""
    total: int
    breaking: int
    non_breaking: int
    by_type: Dict[str, int]

    @property
    def has_breaking(self) -> bool:
        return self.breaking > 0

    @property
    def has_changes(self) -> bool:
        return self.total > 0


def summarize(result: DiffResult) -> DiffSummary:
    """Produce a DiffSummary from a DiffResult."""
    by_type: Dict[str, int] = {}
    breaking_count = 0
    non_breaking_count = 0

    for change in result.changes:
        key = change.change_type.value
        by_type[key] = by_type.get(key, 0) + 1
        if change.breaking:
            breaking_count += 1
        else:
            non_breaking_count += 1

    return DiffSummary(
        total=len(result.changes),
        breaking=breaking_count,
        non_breaking=non_breaking_count,
        by_type=by_type,
    )


def format_summary_text(summary: DiffSummary) -> str:
    """Render a DiffSummary as a human-readable string."""
    lines = []
    lines.append("=== Diff Summary ===")
    lines.append(f"Total changes  : {summary.total}")
    lines.append(f"Breaking       : {summary.breaking}")
    lines.append(f"Non-breaking   : {summary.non_breaking}")
    if summary.by_type:
        lines.append("By change type :")
        for change_type, count in sorted(summary.by_type.items()):
            lines.append(f"  {change_type:<30} {count}")
    return "\n".join(lines)
