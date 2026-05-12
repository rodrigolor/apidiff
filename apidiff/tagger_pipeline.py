"""Pipeline integration for tag-based change grouping."""
from dataclasses import dataclass
from typing import Optional

from apidiff.loader import load_spec
from apidiff.differ import diff_specs
from apidiff.tagger import TagReport, build_tag_report, format_tag_report_text


@dataclass
class TaggerPipelineResult:
    """Result returned by run_tagger_pipeline."""

    report: TagReport
    formatted: str

    @property
    def has_untagged(self) -> bool:
        return len(self.report.untagged) > 0

    @property
    def tag_count(self) -> int:
        return len(self.report.tag_names)


def run_tagger_pipeline(
    base_path: str,
    head_path: str,
    tag_filter: Optional[str] = None,
) -> TaggerPipelineResult:
    """Load two specs, diff them, and produce a tag-grouped report.

    Args:
        base_path: Path to the base OpenAPI spec file.
        head_path: Path to the head (new) OpenAPI spec file.
        tag_filter: If provided, only include changes for this tag.

    Returns:
        TaggerPipelineResult with the grouped report and formatted text.
    """
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)
    diff = diff_specs(base_spec, head_spec)
    report = build_tag_report(diff, base_spec, head_spec)

    if tag_filter:
        filtered_by_tag = {
            k: v for k, v in report.by_tag.items() if k == tag_filter
        }
        from apidiff.tagger import TagReport as TR
        report = TR(by_tag=filtered_by_tag, untagged=[])

    formatted = format_tag_report_text(report)
    return TaggerPipelineResult(report=report, formatted=formatted)
