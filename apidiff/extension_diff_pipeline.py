"""Pipeline wrapper for running extension diff from spec files."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from apidiff.extension_diff import ExtensionDiffResult, diff_extensions
from apidiff.loader import load_spec


@dataclass
class ExtensionDiffPipelineResult:
    """Result returned by the extension diff pipeline."""

    diff: ExtensionDiffResult
    base_path: str
    head_path: str

    @property
    def has_changes(self) -> bool:
        return self.diff.has_changes

    @property
    def total(self) -> int:
        return self.diff.total

    def summary_text(self) -> str:
        if not self.has_changes:
            return "No vendor extension changes detected."
        lines = [f"Vendor extension changes ({self.total}):", ""]
        for change in self.diff.changes:
            lines.append(f"  - {change}")
        return "\n".join(lines)


def run_extension_diff_pipeline(
    base_path: str,
    head_path: str,
) -> ExtensionDiffPipelineResult:
    """Load two spec files and diff their vendor extensions."""
    base_spec: Dict[str, Any] = load_spec(base_path)
    head_spec: Dict[str, Any] = load_spec(head_path)
    result = diff_extensions(base_spec, head_spec)
    return ExtensionDiffPipelineResult(
        diff=result,
        base_path=base_path,
        head_path=head_path,
    )
