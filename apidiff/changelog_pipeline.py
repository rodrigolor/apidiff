"""High-level helper that wires loader → differ → changelog in one call."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from apidiff.loader import load_spec
from apidiff.differ import diff_specs
from apidiff.changelog import ChangelogEntry, build_changelog
from apidiff.changelog_export import export_changelog


def generate_changelog(
    base_path: Union[str, Path],
    head_path: Union[str, Path],
    version: str = "next",
    title: Optional[str] = None,
    output: Optional[Union[str, Path]] = None,
    fmt: str = "text",
) -> ChangelogEntry:
    """Load two spec files, diff them, and return (optionally export) a changelog.

    Parameters
    ----------
    base_path:
        Path to the *old* OpenAPI spec.
    head_path:
        Path to the *new* OpenAPI spec.
    version:
        Version label used in the changelog header.
    title:
        Optional custom title for the changelog section.
    output:
        If provided, the changelog is written to this file path.
    fmt:
        Output format when *output* is set: ``text``, ``markdown``, or ``json``.

    Returns
    -------
    ChangelogEntry
        The structured changelog data.
    """
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)

    result = diff_specs(base_spec, head_spec)
    entry = build_changelog(result, version=version, title=title)

    if output is not None:
        export_changelog(entry, output, fmt=fmt)

    return entry
