"""Export a ChangelogEntry to a file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from apidiff.changelog import ChangelogEntry, format_changelog_text, format_changelog_markdown


class ChangelogExportError(Exception):
    """Raised when changelog export fails."""


def _entry_to_dict(entry: ChangelogEntry) -> dict:
    return {
        "version": entry.version,
        "title": entry.title,
        "breaking": entry.breaking,
        "non_breaking": entry.non_breaking,
    }


def export_changelog(
    entry: ChangelogEntry,
    path: Union[str, Path],
    fmt: str = "text",
) -> None:
    """Export a ChangelogEntry to *path* in the requested format.

    Supported formats: ``text``, ``markdown``, ``json``.
    """
    path = Path(path)
    fmt = fmt.lower()

    if fmt == "json":
        content = json.dumps(_entry_to_dict(entry), indent=2)
    elif fmt in ("markdown", "md"):
        content = format_changelog_markdown(entry)
    elif fmt == "text":
        content = format_changelog_text(entry)
    else:
        raise ChangelogExportError(f"Unsupported changelog format: {fmt!r}")

    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ChangelogExportError(f"Failed to write changelog to {path}: {exc}") from exc
