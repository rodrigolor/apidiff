"""Pipeline wrapper for constraint diff."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from apidiff.loader import load_spec
from apidiff.constraint_diff import ConstraintDiffResult, diff_constraints


@dataclass
class ConstraintDiffPipelineResult:
    result: ConstraintDiffResult
    base_path: str
    head_path: str

    def has_breaking(self) -> bool:
        return self.result.has_breaking()

    def has_changes(self) -> bool:
        return self.result.has_changes()

    def total(self) -> int:
        return self.result.total()

    def summary_text(self) -> str:
        if not self.result.has_changes():
            return "No constraint changes detected."
        lines = [f"Constraint changes ({self.result.total()} total):"]
        for change in self.result.changes:
            tag = "[BREAKING]" if change.is_breaking() else "[non-breaking]"
            lines.append(f"  {tag} {change}")
        return "\n".join(lines)


def run_constraint_diff_pipeline(
    base_path: str,
    head_path: str,
) -> ConstraintDiffPipelineResult:
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)
    result = diff_constraints(base_spec, head_spec)
    return ConstraintDiffPipelineResult(
        result=result,
        base_path=base_path,
        head_path=head_path,
    )
