"""High-level pipeline that combines diffing with stats computation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from apidiff.differ import DiffResult, diff_specs
from apidiff.stats import DiffStats, compute_stats, format_stats_text


@dataclass
class StatsPipelineResult:
    diff: DiffResult
    stats: DiffStats

    @property
    def has_breaking(self) -> bool:
        return self.stats.breaking > 0

    @property
    def has_changes(self) -> bool:
        return self.stats.total > 0


def run_stats_pipeline(
    base_spec: dict,
    new_spec: dict,
    path_prefix: Optional[str] = None,
) -> StatsPipelineResult:
    """Diff *base_spec* against *new_spec*, then compute stats.

    Parameters
    ----------
    base_spec:
        The original OpenAPI spec dictionary.
    new_spec:
        The updated OpenAPI spec dictionary.
    path_prefix:
        If given, only changes whose path starts with this prefix are included.
    """
    result = diff_specs(base_spec, new_spec)

    if path_prefix:
        filtered = [
            c for c in result.changes
            if c.path and c.path.startswith(path_prefix)
        ]
        from apidiff.differ import DiffResult as DR  # local import to avoid circularity
        result = DR(changes=filtered)

    stats = compute_stats(result)
    return StatsPipelineResult(diff=result, stats=stats)


def format_pipeline_stats(pipeline_result: StatsPipelineResult) -> str:
    """Return a formatted text summary of the pipeline stats."""
    return format_stats_text(pipeline_result.stats)
