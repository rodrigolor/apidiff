"""Pipeline helper that loads specs and produces a CoverageResult."""

from dataclasses import dataclass

from apidiff.loader import load_spec
from apidiff.differ import diff_specs
from apidiff.path_coverage import CoverageResult, compute_path_coverage, format_coverage_text


@dataclass
class CoveragePipelineResult:
    coverage: CoverageResult
    base_path: str
    head_path: str

    @property
    def has_changes(self) -> bool:
        return self.coverage.changed_paths > 0

    @property
    def summary_text(self) -> str:
        return format_coverage_text(self.coverage)


def run_coverage_pipeline(base_path: str, head_path: str) -> CoveragePipelineResult:
    """Load two spec files, diff them, and return coverage metrics."""
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)
    diff = diff_specs(base_spec, head_spec)
    coverage = compute_path_coverage(base_spec, head_spec, diff)
    return CoveragePipelineResult(
        coverage=coverage,
        base_path=base_path,
        head_path=head_path,
    )
