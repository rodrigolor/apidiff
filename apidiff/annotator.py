"""Annotate diff results with human-readable descriptions and metadata."""

from dataclasses import dataclass, field
from typing import List, Optional

from apidiff.differ import Change, ChangeType, DiffResult


@dataclass
class AnnotatedChange:
    """A change decorated with additional descriptive metadata."""

    change: Change
    title: str
    description: str
    migration_hint: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def is_breaking(self) -> bool:
        return self.change.change_type == ChangeType.BREAKING


_TITLES = {
    "endpoint_removed": "Endpoint Removed",
    "endpoint_added": "Endpoint Added",
    "operation_removed": "Operation Removed",
    "operation_added": "Operation Added",
    "parameter_removed": "Parameter Removed",
    "parameter_added": "Parameter Added",
    "response_changed": "Response Schema Changed",
    "request_body_changed": "Request Body Changed",
}

_HINTS = {
    "endpoint_removed": "Update all clients to stop calling this endpoint before removing it.",
    "operation_removed": "Ensure no clients rely on this HTTP method for the path.",
    "parameter_removed": "Check that no client sends this parameter; it will be ignored or cause errors.",
    "response_changed": "Verify client deserialization logic handles the updated response schema.",
    "request_body_changed": "Validate that client request payloads conform to the new schema.",
}


def _make_description(change: Change) -> str:
    parts = [f"Change type: {change.change_type.value}"]
    if change.path:
        parts.append(f"Path: {change.path}")
    if change.method:
        parts.append(f"Method: {change.method.upper()}")
    if change.detail:
        parts.append(f"Detail: {change.detail}")
    return " | ".join(parts)


def annotate_change(change: Change) -> AnnotatedChange:
    """Wrap a single Change with descriptive metadata."""
    key = change.field or ""
    title = _TITLES.get(key, key.replace("_", " ").title() if key else "Unknown Change")
    description = _make_description(change)
    hint = _HINTS.get(key)
    tags = [change.change_type.value]
    if change.method:
        tags.append(change.method.upper())
    return AnnotatedChange(
        change=change,
        title=title,
        description=description,
        migration_hint=hint,
        tags=tags,
    )


def annotate_result(result: DiffResult) -> List[AnnotatedChange]:
    """Return a list of AnnotatedChange objects for all changes in a DiffResult."""
    return [annotate_change(c) for c in result.changes]


def format_annotated_text(annotated: List[AnnotatedChange]) -> str:
    """Render annotated changes as a human-readable text report."""
    if not annotated:
        return "No changes to annotate.\n"
    lines = []
    for item in annotated:
        severity = "[BREAKING]" if item.is_breaking() else "[non-breaking]"
        lines.append(f"{severity} {item.title}")
        lines.append(f"  {item.description}")
        if item.migration_hint:
            lines.append(f"  Hint: {item.migration_hint}")
        if item.tags:
            lines.append(f"  Tags: {', '.join(item.tags)}")
        lines.append("")
    return "\n".join(lines)
