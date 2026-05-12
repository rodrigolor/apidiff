"""Pipeline entry point: load two specs, diff them, and produce a ComparisonReport."""

from dataclasses import dataclass
from typing import Optional

from apidiff.loader import load_spec
from apidiff.differ import diff_specs
from apidiff.comparator import ComparisonReport, build_comparison_report, format_comparison_text
from apidiff.filter import filter_breaking, filter_non_breaking
from apidiff.ignorer import IgnoreConfig


@dataclass
class ComparatorPipelineResult:
    """Output of run_comparator_pipeline."""

    report: ComparisonReport
    text: str

    @property
    def has_breaking(self) -> bool:
        return self.report.total_breaking > 0

    @property
    def has_changes(self) -> bool:
        return self.report.total_changes > 0


def run_comparator_pipeline(
    base_path: str,
    head_path: str,
    breaking_only: bool = False,
    non_breaking_only: bool = False,
    ignore_config: Optional[IgnoreConfig] = None,
) -> ComparatorPipelineResult:
    """Load specs, diff, optionally filter, and build a ComparisonReport."""
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)

    diff_result = diff_specs(base_spec, head_spec)

    if ignore_config is not None:
        diff_result = ignore_config.apply(diff_result)

    if breaking_only:
        diff_result = filter_breaking(diff_result)
    elif non_breaking_only:
        diff_result = filter_non_breaking(diff_result)

    report = build_comparison_report(diff_result)
    text = format_comparison_text(report)

    return ComparatorPipelineResult(report=report, text=text)
