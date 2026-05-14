"""Path coverage analysis: measures how much of the API surface changed."""

from dataclasses import dataclass, field
from typing import Set

from apidiff.differ import DiffResult, ChangeType


@dataclass
class CoverageResult:
    total_paths: int
    changed_paths: int
    added_paths: Set[str] = field(default_factory=set)
    removed_paths: Set[str] = field(default_factory=set)
    modified_paths: Set[str] = field(default_factory=set)

    @property
    def coverage_ratio(self) -> float:
        """Fraction of paths that have at least one change."""
        if self.total_paths == 0:
            return 0.0
        return self.changed_paths / self.total_paths

    @property
    def coverage_percent(self) -> float:
        return round(self.coverage_ratio * 100, 2)


def _collect_spec_paths(spec: dict) -> Set[str]:
    """Return the set of path strings defined in an OpenAPI spec."""
    return set((spec.get("paths") or {}).keys())


def compute_path_coverage(
    base_spec: dict,
    head_spec: dict,
    result: DiffResult,
) -> CoverageResult:
    """Compute which paths were touched by the diff."""
    base_paths = _collect_spec_paths(base_spec)
    head_paths = _collect_spec_paths(head_spec)
    all_paths = base_paths | head_paths

    added: Set[str] = set()
    removed: Set[str] = set()
    modified: Set[str] = set()

    for change in result.changes:
        path = change.path or ""
        if not path:
            continue
        if change.change_type == ChangeType.ENDPOINT_ADDED:
            added.add(path)
        elif change.change_type == ChangeType.ENDPOINT_REMOVED:
            removed.add(path)
        else:
            modified.add(path)

    changed = added | removed | modified

    return CoverageResult(
        total_paths=len(all_paths),
        changed_paths=len(changed),
        added_paths=added,
        removed_paths=removed,
        modified_paths=modified,
    )


def format_coverage_text(coverage: CoverageResult) -> str:
    """Return a human-readable summary of path coverage."""
    lines = [
        f"Path coverage: {coverage.changed_paths}/{coverage.total_paths} "
        f"({coverage.coverage_percent}%)",
        f"  Added   : {len(coverage.added_paths)}",
        f"  Removed : {len(coverage.removed_paths)}",
        f"  Modified: {len(coverage.modified_paths)}",
    ]
    return "\n".join(lines)
