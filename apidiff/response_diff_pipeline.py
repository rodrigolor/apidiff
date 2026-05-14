"""Pipeline wrapper for response diff operations."""
from __future__ import annotations

from dataclasses import dataclass, field

from apidiff.loader import load_spec
from apidiff.response_diff import ResponseChange, diff_responses, is_breaking_response_change


@dataclass
class ResponseDiffPipelineResult:
    changes: list[ResponseChange] = field(default_factory=list)
    breaking: list[ResponseChange] = field(default_factory=list)
    non_breaking: list[ResponseChange] = field(default_factory=list)

    @property
    def has_breaking(self) -> bool:
        return len(self.breaking) > 0

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def total(self) -> int:
        return len(self.changes)


def run_response_diff_pipeline(base_path: str, head_path: str) -> ResponseDiffPipelineResult:
    """Load two spec files and return a ResponseDiffPipelineResult."""
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)
    changes = diff_responses(base_spec, head_spec)
    breaking = [c for c in changes if is_breaking_response_change(c)]
    non_breaking = [c for c in changes if not is_breaking_response_change(c)]
    return ResponseDiffPipelineResult(
        changes=changes,
        breaking=breaking,
        non_breaking=non_breaking,
    )


def format_pipeline_result(result: ResponseDiffPipelineResult) -> str:
    """Format the pipeline result as a human-readable string."""
    if not result.has_changes:
        return "No response changes detected."
    lines = [f"Response changes: {result.total} total, "
             f"{len(result.breaking)} breaking, "
             f"{len(result.non_breaking)} non-breaking"]
    for rc in result.changes:
        tag = "[BREAKING]" if is_breaking_response_change(rc) else "[non-breaking]"
        lines.append(f"  {tag} {rc}")
    return "\n".join(lines)
