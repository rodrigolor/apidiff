"""Output formatters for diff results."""

from typing import TextIO
import sys

from apidiff.differ import ChangeType, DiffResult

ANSI_RESET = "\033[0m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def format_text(result: DiffResult, out: TextIO = sys.stdout, use_color: bool = True) -> None:
    """Write a human-readable diff report to *out*."""
    if not result.changes:
        out.write(_colorize("No changes detected.\n", ANSI_GREEN, use_color))
        return

    breaking = result.breaking
    non_breaking = result.non_breaking
    info_changes = [c for c in result.changes if c.change_type == ChangeType.INFO]

    if breaking:
        out.write(_colorize(f"Breaking changes ({len(breaking)}):\n", ANSI_BOLD + ANSI_RED, use_color))
        for change in breaking:
            line = f"  {change.path}: {change.message}\n"
            out.write(_colorize(line, ANSI_RED, use_color))

    if non_breaking:
        out.write(_colorize(f"Non-breaking changes ({len(non_breaking)}):\n", ANSI_BOLD + ANSI_GREEN, use_color))
        for change in non_breaking:
            line = f"  {change.path}: {change.message}\n"
            out.write(_colorize(line, ANSI_GREEN, use_color))

    if info_changes:
        out.write(_colorize(f"Info ({len(info_changes)}):\n", ANSI_BOLD + ANSI_YELLOW, use_color))
        for change in info_changes:
            line = f"  {change.path}: {change.message}\n"
            out.write(_colorize(line, ANSI_YELLOW, use_color))

    summary = f"\nSummary: {len(breaking)} breaking, {len(non_breaking)} non-breaking, {len(info_changes)} info\n"
    out.write(summary)


def format_json(result: DiffResult) -> dict:
    """Return a JSON-serialisable dict representing the diff result."""
    return {
        "has_breaking_changes": result.has_breaking_changes,
        "summary": {
            "breaking": len(result.breaking),
            "non_breaking": len(result.non_breaking),
            "info": len([c for c in result.changes if c.change_type == ChangeType.INFO]),
        },
        "changes": [
            {
                "type": change.change_type.value,
                "path": change.path,
                "message": change.message,
                "old_value": change.old_value,
                "new_value": change.new_value,
            }
            for change in result.changes
        ],
    }
