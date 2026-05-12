"""Fluent pipeline for filtering, sorting, and exporting diff results."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from apidiff.differ import DiffResult
from apidiff.filter import filter_breaking, filter_non_breaking, filter_by_path, filter_by_method
from apidiff.sorter import sort_changes
from apidiff.exporter import export_result


class DiffPipeline:
    """Chain filter/sort/export operations on a :class:`DiffResult`."""

    def __init__(self, result: DiffResult) -> None:
        self._result = result

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def breaking_only(self) -> "DiffPipeline":
        """Keep only breaking changes."""
        return DiffPipeline(filter_breaking(self._result))

    def non_breaking_only(self) -> "DiffPipeline":
        """Keep only non-breaking changes."""
        return DiffPipeline(filter_non_breaking(self._result))

    def path(self, pattern: str) -> "DiffPipeline":
        """Keep changes whose path contains *pattern*."""
        return DiffPipeline(filter_by_path(self._result, pattern))

    def method(self, http_method: str) -> "DiffPipeline":
        """Keep changes matching *http_method* (case-insensitive)."""
        return DiffPipeline(filter_by_method(self._result, http_method))

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort(self, by: str = "severity", ascending: bool = True) -> "DiffPipeline":
        """Sort changes. *by* is ``'severity'`` or ``'path'``."""
        return DiffPipeline(sort_changes(self._result, by=by, ascending=ascending))

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export(
        self,
        dest: str | Path,
        fmt: str = "json",
    ) -> Path:
        """Write the current result to *dest* and return the resolved path."""
        return export_result(self._result, dest, fmt=fmt)

    # ------------------------------------------------------------------
    # Terminal
    # ------------------------------------------------------------------

    def result(self) -> DiffResult:
        """Return the current :class:`DiffResult`."""
        return self._result

    def __len__(self) -> int:  # pragma: no cover
        return len(self._result.changes)
