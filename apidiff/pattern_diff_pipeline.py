"""Pipeline wrapper for pattern diff: load specs from files and run diff."""

from __future__ import annotations

from dataclasses import dataclass

from apidiff.loader import load_spec
from apidiff.pattern_diff import PatternDiffResult, diff_patterns


@dataclass
class PatternDiffPipelineResult:
    result: PatternDiffResult
    base_path: str
    head_path: str

    def has_breaking(self) -> bool:
        return self.result.has_breaking()

    def has_changes(self) -> bool:
        return self.result.has_changes()

    def total(self) -> int:
        return self.result.total()

    def summary_text(self) -> str:
        r = self.result
        if not r.has_changes():
            return "No pattern changes detected."
        lines = [f"Pattern changes: {r.total()} total"]
        if r.has_breaking():
            lines.append(f"  Breaking : {len(r.breaking())}")
        non_b = len(r.non_breaking())
        if non_b:
            lines.append(f"  Non-breaking: {non_b}")
        return "\n".join(lines)


def run_pattern_diff_pipeline(base_path: str, head_path: str) -> PatternDiffPipelineResult:
    """Load two spec files and return a PatternDiffPipelineResult."""
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)
    result = diff_patterns(base_spec, head_spec)
    return PatternDiffPipelineResult(
        result=result,
        base_path=base_path,
        head_path=head_path,
    )
