"""Tag changes based on OpenAPI tags metadata."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from apidiff.differ import Change, DiffResult


@dataclass
class TaggedChange:
    """A change annotated with its associated OpenAPI tags."""

    change: Change
    tags: List[str] = field(default_factory=list)

    @property
    def primary_tag(self) -> Optional[str]:
        """Return the first tag, if any."""
        return self.tags[0] if self.tags else None


@dataclass
class TagReport:
    """Groups tagged changes by tag name."""

    by_tag: Dict[str, List[TaggedChange]] = field(default_factory=dict)
    untagged: List[TaggedChange] = field(default_factory=list)

    @property
    def tag_names(self) -> List[str]:
        return sorted(self.by_tag.keys())

    @property
    def total(self) -> int:
        total = sum(len(v) for v in self.by_tag.values())
        return total + len(self.untagged)


def _extract_tags(path: Optional[str], method: Optional[str], spec: dict) -> List[str]:
    """Extract tags for a given path+method from a spec dict."""
    if not path or not method:
        return []
    try:
        operation = spec.get("paths", {}).get(path, {}).get(method.lower(), {})
        return list(operation.get("tags", []))
    except (AttributeError, TypeError):
        return []


def tag_change(change: Change, base_spec: dict, head_spec: dict) -> TaggedChange:
    """Annotate a single change with tags from base or head spec."""
    tags = _extract_tags(change.path, change.method, head_spec)
    if not tags:
        tags = _extract_tags(change.path, change.method, base_spec)
    return TaggedChange(change=change, tags=tags)


def build_tag_report(
    result: DiffResult, base_spec: dict, head_spec: dict
) -> TagReport:
    """Build a TagReport grouping all changes by their OpenAPI tags."""
    report = TagReport()
    for change in result.changes:
        tagged = tag_change(change, base_spec, head_spec)
        if tagged.tags:
            for tag in tagged.tags:
                report.by_tag.setdefault(tag, []).append(tagged)
        else:
            report.untagged.append(tagged)
    return report


def format_tag_report_text(report: TagReport) -> str:
    """Format a TagReport as human-readable text."""
    lines = []
    for tag in report.tag_names:
        changes = report.by_tag[tag]
        lines.append(f"[{tag}] ({len(changes)} change(s))")
        for tc in changes:
            severity = "BREAKING" if tc.change.breaking else "non-breaking"
            lines.append(f"  {severity}: {tc.change.change_type.value} {tc.change.path}")
    if report.untagged:
        lines.append(f"[untagged] ({len(report.untagged)} change(s))")
        for tc in report.untagged:
            severity = "BREAKING" if tc.change.breaking else "non-breaking"
            lines.append(f"  {severity}: {tc.change.change_type.value} {tc.change.path}")
    if not lines:
        return "No changes to tag."
    return "\n".join(lines)
