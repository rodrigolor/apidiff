"""Filtering utilities for diff results."""

from typing import List, Optional
from apidiff.differ import Change, ChangeType, DiffResult


def filter_by_change_type(
    result: DiffResult, change_type: ChangeType
) -> DiffResult:
    """Return a new DiffResult containing only changes of the given type."""
    filtered = [c for c in result.changes if c.change_type == change_type]
    return DiffResult(changes=filtered)


def filter_breaking(result: DiffResult) -> DiffResult:
    """Return a new DiffResult containing only breaking changes."""
    filtered = [c for c in result.changes if c.change_type == ChangeType.BREAKING]
    return DiffResult(changes=filtered)


def filter_non_breaking(result: DiffResult) -> DiffResult:
    """Return a new DiffResult containing only non-breaking changes."""
    filtered = [
        c for c in result.changes if c.change_type == ChangeType.NON_BREAKING
    ]
    return DiffResult(changes=filtered)


def filter_by_path(result: DiffResult, path_prefix: str) -> DiffResult:
    """Return a new DiffResult with changes whose path starts with path_prefix."""
    filtered = [
        c for c in result.changes if c.path.startswith(path_prefix)
    ]
    return DiffResult(changes=filtered)


def filter_by_method(
    result: DiffResult, method: str
) -> DiffResult:
    """Return a new DiffResult with changes matching the given HTTP method."""
    method_lower = method.lower()
    filtered = [
        c for c in result.changes
        if len(c.path.split(".")) > 1
        and c.path.split(".")[1].lower() == method_lower
    ]
    return DiffResult(changes=filtered)


def apply_filters(
    result: DiffResult,
    breaking_only: bool = False,
    non_breaking_only: bool = False,
    path_prefix: Optional[str] = None,
    method: Optional[str] = None,
) -> DiffResult:
    """Apply multiple filters to a DiffResult in sequence."""
    filtered = result
    if breaking_only:
        filtered = filter_breaking(filtered)
    elif non_breaking_only:
        filtered = filter_non_breaking(filtered)
    if path_prefix:
        filtered = filter_by_path(filtered, path_prefix)
    if method:
        filtered = filter_by_method(filtered, method)
    return filtered
