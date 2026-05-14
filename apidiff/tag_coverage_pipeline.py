"""Pipeline entry-point for tag-coverage analysis of two spec files."""
from __future__ import annotations

from dataclasses import dataclass

from apidiff.loader import load_spec
from apidiff.tag_coverage import (
    TagCoverageResult,
    compute_tag_coverage,
    format_tag_coverage_text,
)


@dataclass
class TagCoveragePipelineResult:
    base: TagCoverageResult
    head: TagCoverageResult
    base_path: str
    head_path: str

    @property
    def coverage_dropped(self) -> bool:
        """True when head coverage ratio is lower than base."""
        return self.head.coverage_ratio < self.base.coverage_ratio

    @property
    def summary_text(self) -> str:
        lines = [
            f"=== Tag Coverage: {self.base_path} ===",
            format_tag_coverage_text(self.base),
            "",
            f"=== Tag Coverage: {self.head_path} ===",
            format_tag_coverage_text(self.head),
        ]
        if self.coverage_dropped:
            lines.append(
                "\n[WARNING] Tag coverage decreased from "
                f"{self.base.coverage_percent}% to {self.head.coverage_percent}%"
            )
        return "\n".join(lines)


def run_tag_coverage_pipeline(
    base_path: str,
    head_path: str,
) -> TagCoveragePipelineResult:
    """Load two spec files and compute tag coverage for each."""
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)
    return TagCoveragePipelineResult(
        base=compute_tag_coverage(base_spec),
        head=compute_tag_coverage(head_spec),
        base_path=base_path,
        head_path=head_path,
    )
