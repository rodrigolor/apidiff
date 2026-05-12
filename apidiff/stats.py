"""Compute statistics over a DiffResult for reporting and dashboards."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from apidiff.differ import ChangeType, DiffResult


@dataclass
class DiffStats:
    total: int = 0
    breaking: int = 0
    non_breaking: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_method: Dict[str, int] = field(default_factory=dict)
    by_path: Dict[str, int] = field(default_factory=dict)
    affected_paths: List[str] = field(default_factory=list)

    @property
    def breaking_ratio(self) -> float:
        """Fraction of changes that are breaking (0.0–1.0)."""
        if self.total == 0:
            return 0.0
        return self.breaking / self.total


def compute_stats(result: DiffResult) -> DiffStats:
    """Return a :class:`DiffStats` summary for *result*."""
    stats = DiffStats()
    seen_paths: set = set()

    for change in result.changes:
        stats.total += 1

        if change.change_type in (
            ChangeType.BREAKING,
        ):
            stats.breaking += 1
        else:
            stats.non_breaking += 1

        type_key = change.change_type.value
        stats.by_type[type_key] = stats.by_type.get(type_key, 0) + 1

        if change.method:
            method_key = change.method.upper()
            stats.by_method[method_key] = stats.by_method.get(method_key, 0) + 1

        if change.path:
            stats.by_path[change.path] = stats.by_path.get(change.path, 0) + 1
            seen_paths.add(change.path)

    stats.affected_paths = sorted(seen_paths)
    return stats


def format_stats_text(stats: DiffStats) -> str:
    """Render *stats* as a human-readable text block."""
    lines = [
        f"Total changes   : {stats.total}",
        f"Breaking        : {stats.breaking}",
        f"Non-breaking    : {stats.non_breaking}",
        f"Breaking ratio  : {stats.breaking_ratio:.0%}",
    ]
    if stats.by_method:
        lines.append("By method:")
        for method, count in sorted(stats.by_method.items()):
            lines.append(f"  {method}: {count}")
    if stats.affected_paths:
        lines.append(f"Affected paths  : {len(stats.affected_paths)}")
    return "\n".join(lines)
