"""Pipeline for applying filter and sort operations to a DiffResult."""

from typing import Optional
from apidiff.differ import DiffResult
from apidiff.filter import apply_filters
from apidiff.sorter import sort_changes


class DiffPipeline:
    """Fluent interface for filtering and sorting a DiffResult."""

    def __init__(self, result: DiffResult) -> None:
        self._result = result

    def breaking_only(self) -> "DiffPipeline":
        """Keep only breaking changes."""
        self._result = apply_filters(self._result, breaking_only=True)
        return self

    def non_breaking_only(self) -> "DiffPipeline":
        """Keep only non-breaking changes."""
        self._result = apply_filters(self._result, non_breaking_only=True)
        return self

    def path(self, prefix: str) -> "DiffPipeline":
        """Keep only changes whose path starts with prefix."""
        self._result = apply_filters(self._result, path_prefix=prefix)
        return self

    def method(self, http_method: str) -> "DiffPipeline":
        """Keep only changes for the given HTTP method."""
        self._result = apply_filters(self._result, method=http_method)
        return self

    def sort(self, by: str = "severity", reverse: bool = False) -> "DiffPipeline":
        """Sort changes by the given key ('severity' or 'path')."""
        self._result = sort_changes(self._result, by=by, reverse=reverse)
        return self

    def result(self) -> DiffResult:
        """Return the final DiffResult after all pipeline steps."""
        return self._result


def build_pipeline(result: DiffResult) -> DiffPipeline:
    """Create a new DiffPipeline for the given result."""
    return DiffPipeline(result)
