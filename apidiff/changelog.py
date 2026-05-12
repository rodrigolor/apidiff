"""Generate a human-readable changelog from a DiffResult."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from apidiff.differ import ChangeType, DiffResult


@dataclass
class ChangelogEntry:
    version: str
    title: str
    breaking: List[str] = field(default_factory=list)
    non_breaking: List[str] = field(default_factory=list)


def _describe_change(change) -> str:
    """Return a short human-readable description of a single Change."""
    method = change.method.upper() if change.method else ""
    location = f"{method} {change.path}" if method else change.path
    return f"{change.change_type.value}: {location} — {change.description}"


def build_changelog(
    result: DiffResult,
    version: str = "next",
    title: Optional[str] = None,
) -> ChangelogEntry:
    """Build a ChangelogEntry from a DiffResult."""
    entry_title = title or f"API changes for version {version}"
    entry = ChangelogEntry(version=version, title=entry_title)

    for change in result.changes:
        description = _describe_change(change)
        if change.breaking:
            entry.breaking.append(description)
        else:
            entry.non_breaking.append(description)

    return entry


def format_changelog_text(entry: ChangelogEntry) -> str:
    """Render a ChangelogEntry as plain text."""
    lines = [f"## {entry.title} ({entry.version})", ""]

    if entry.breaking:
        lines.append("### Breaking Changes")
        for item in entry.breaking:
            lines.append(f"  - {item}")
        lines.append("")

    if entry.non_breaking:
        lines.append("### Non-Breaking Changes")
        for item in entry.non_breaking:
            lines.append(f"  - {item}")
        lines.append("")

    if not entry.breaking and not entry.non_breaking:
        lines.append("No changes detected.")
        lines.append("")

    return "\n".join(lines)


def format_changelog_markdown(entry: ChangelogEntry) -> str:
    """Render a ChangelogEntry as Markdown."""
    return format_changelog_text(entry)
