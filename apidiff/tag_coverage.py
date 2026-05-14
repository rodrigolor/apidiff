"""Compute tag coverage: how many paths/operations are tagged in each spec."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TagCoverageResult:
    total_operations: int = 0
    tagged_operations: int = 0
    untagged_paths: List[str] = field(default_factory=list)
    tag_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def coverage_ratio(self) -> float:
        if self.total_operations == 0:
            return 1.0
        return self.tagged_operations / self.total_operations

    @property
    def coverage_percent(self) -> float:
        return round(self.coverage_ratio * 100, 2)

    @property
    def is_fully_tagged(self) -> bool:
        return self.total_operations > 0 and self.tagged_operations == self.total_operations


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


def compute_tag_coverage(spec: dict) -> TagCoverageResult:
    """Analyse a loaded OpenAPI spec dict and return tag coverage statistics."""
    result = TagCoverageResult()
    paths = spec.get("paths") or {}

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        path_untagged = False
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue
            result.total_operations += 1
            tags = operation.get("tags") or []
            if tags:
                result.tagged_operations += 1
                for tag in tags:
                    result.tag_counts[tag] = result.tag_counts.get(tag, 0) + 1
            else:
                path_untagged = True
        if path_untagged and path not in result.untagged_paths:
            result.untagged_paths.append(path)

    return result


def format_tag_coverage_text(result: TagCoverageResult) -> str:
    """Return a human-readable summary of tag coverage."""
    lines = [
        f"Tag Coverage: {result.tagged_operations}/{result.total_operations} "
        f"operations tagged ({result.coverage_percent}%)",
    ]
    if result.untagged_paths:
        lines.append("Untagged paths:")
        for p in sorted(result.untagged_paths):
            lines.append(f"  {p}")
    if result.tag_counts:
        lines.append("Tag usage:")
        for tag, count in sorted(result.tag_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {tag}: {count}")
    return "\n".join(lines)
