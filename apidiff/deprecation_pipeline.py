"""High-level pipeline for running deprecation analysis as part of a diff workflow."""

from dataclasses import dataclass
from typing import Optional

from apidiff.deprecation import (
    DeprecationReport,
    scan_deprecations,
    scan_spec_deprecations,
    format_deprecation_report,
)
from apidiff.differ import DiffResult


@dataclass
class DeprecationPipelineResult:
    diff_deprecations: DeprecationReport
    new_spec_deprecations: DeprecationReport

    @property
    def total_count(self) -> int:
        return self.diff_deprecations.count + self.new_spec_deprecations.count

    @property
    def has_any(self) -> bool:
        return self.total_count > 0


def run_deprecation_pipeline(
    diff_result: DiffResult,
    new_spec: Optional[dict] = None,
) -> DeprecationPipelineResult:
    """Run full deprecation analysis against a diff result and optionally the new spec."""
    diff_report = scan_deprecations(diff_result)
    spec_report = scan_spec_deprecations(new_spec) if new_spec is not None else DeprecationReport()
    return DeprecationPipelineResult(
        diff_deprecations=diff_report,
        new_spec_deprecations=spec_report,
    )


def format_pipeline_result(pipeline_result: DeprecationPipelineResult) -> str:
    """Format the combined deprecation pipeline result as a human-readable string."""
    sections = []

    sections.append("=== Changes Introducing Deprecations ===")
    sections.append(format_deprecation_report(pipeline_result.diff_deprecations))

    sections.append("=== Existing Deprecations in New Spec ===")
    sections.append(format_deprecation_report(pipeline_result.new_spec_deprecations))

    return "\n".join(sections)
