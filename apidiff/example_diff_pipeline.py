"""Pipeline wrapper for example diffing."""
from __future__ import annotations

from dataclasses import dataclass

from apidiff.loader import load_spec
from apidiff.example_diff import ExampleDiffResult, diff_examples


@dataclass
class ExampleDiffPipelineResult:
    result: ExampleDiffResult
    base_path: str
    head_path: str

    def has_changes(self) -> bool:
        return self.result.has_changes()

    def total(self) -> int:
        return self.result.total()

    def summary_text(self) -> str:
        if not self.has_changes():
            return "No example changes detected."
        lines = [f"Example changes ({self.total()} total):\n"]
        for change in self.result.changes:
            lines.append(f"  {change}")
        return "\n".join(lines)


def run_example_diff_pipeline(base_path: str, head_path: str) -> ExampleDiffPipelineResult:
    """Load two spec files and return an ExampleDiffPipelineResult."""
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)
    result = diff_examples(base_spec, head_spec)
    return ExampleDiffPipelineResult(
        result=result,
        base_path=base_path,
        head_path=head_path,
    )
