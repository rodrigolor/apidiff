"""Pipeline wrapper for media type diffing."""
from __future__ import annotations

from dataclasses import dataclass

from apidiff.loader import load_spec
from apidiff.media_type_diff import MediaTypeDiffResult, diff_media_types


@dataclass
class MediaTypeDiffPipelineResult:
    result: MediaTypeDiffResult
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
            return "No media type changes detected."
        breaking = sum(1 for c in r.changes if c.is_breaking())
        non_breaking = r.total() - breaking
        parts = [f"Media type changes: {r.total()} total"]
        if breaking:
            parts.append(f"{breaking} breaking")
        if non_breaking:
            parts.append(f"{non_breaking} non-breaking")
        return ", ".join(parts) + "."


def run_media_type_diff_pipeline(
    base_path: str, head_path: str
) -> MediaTypeDiffPipelineResult:
    """Load two spec files and run media type diffing."""
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)
    result = diff_media_types(base_spec, head_spec)
    return MediaTypeDiffPipelineResult(
        result=result,
        base_path=base_path,
        head_path=head_path,
    )
