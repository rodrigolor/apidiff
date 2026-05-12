"""Export diff results to various file formats (JSON, Markdown, plain text)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from apidiff.differ import DiffResult
from apidiff.formatter import format_text, format_json


class ExportError(Exception):
    """Raised when an export operation fails."""


SUPPORTED_FORMATS = ("json", "markdown", "text")


def _to_markdown(result: DiffResult) -> str:
    """Render a DiffResult as a Markdown document."""
    lines = ["# API Diff Report", ""]
    if not result.changes:
        lines.append("_No changes detected._")
        return "\n".join(lines)

    breaking = [c for c in result.changes if c.breaking]
    non_breaking = [c for c in result.changes if not c.breaking]

    if breaking:
        lines.append("## 🚨 Breaking Changes")
        for change in breaking:
            lines.append(f"- **[{change.change_type.value}]** `{change.path}` `{change.method}` — {change.description}")
        lines.append("")

    if non_breaking:
        lines.append("## ℹ️ Non-Breaking Changes")
        for change in non_breaking:
            lines.append(f"- **[{change.change_type.value}]** `{change.path}` `{change.method}` — {change.description}")
        lines.append("")

    return "\n".join(lines)


def export_result(
    result: DiffResult,
    dest: Union[str, Path],
    fmt: str = "json",
) -> Path:
    """Write *result* to *dest* in the requested format.

    Parameters
    ----------
    result:
        The diff result to export.
    dest:
        Destination file path.
    fmt:
        One of ``'json'``, ``'markdown'``, or ``'text'``.

    Returns
    -------
    Path
        The resolved path of the written file.
    """
    fmt = fmt.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    dest = Path(dest)

    try:
        if fmt == "json":
            content = format_json(result)
        elif fmt == "markdown":
            content = _to_markdown(result)
        else:
            content = format_text(result, use_color=False)

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ExportError(f"Failed to write export file '{dest}': {exc}") from exc

    return dest.resolve()
