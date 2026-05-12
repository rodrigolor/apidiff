"""Fluent pipeline for filtering, sorting, validating, and formatting diff results."""

from typing import List, Optional

from apidiff.differ import DiffResult
from apidiff.filter import (
    filter_breaking,
    filter_non_breaking,
    filter_by_path,
    filter_by_method,
)
from apidiff.sorter import sort_changes
from apidiff.formatter import format_text, format_json
from apidiff.validator import ValidationResult, run_validations


class DiffPipeline:
    """Chainable pipeline for processing a DiffResult."""

    def __init__(self, result: DiffResult) -> None:
        self._result = result

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
        """Keep changes for a specific HTTP method."""
        return DiffPipeline(filter_by_method(self._result, http_method))

    def sort(self, by: str = "severity", ascending: bool = True) -> "DiffPipeline":
        """Sort changes by *by* ('severity' or 'path')."""
        return DiffPipeline(sort_changes(self._result, by=by, ascending=ascending))

    def validate(self, rules: Optional[List[str]] = None) -> ValidationResult:
        """Run validation rules and return a ValidationResult."""
        if rules is None:
            rules = ["no-breaking-changes"]
        return run_validations(self._result, rules)

    def to_text(self, color: bool = True) -> str:
        """Render the current result as plain text."""
        return format_text(self._result, color=color)

    def to_json(self) -> str:
        """Render the current result as JSON."""
        return format_json(self._result)

    def result(self) -> DiffResult:
        """Return the underlying DiffResult."""
        return self._result

    def __len__(self) -> int:
        return len(self._result.changes)
