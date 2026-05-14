"""Sorting utilities for diff results."""

from typing import List
from apidiff.differ import Change, ChangeType, DiffResult


def sort_by_path(result: DiffResult, reverse: bool = False) -> DiffResult:
    """Return a new DiffResult with changes sorted alphabetically by path."""
    sorted_changes = sorted(result.changes, key=lambda c: c.path, reverse=reverse)
    return DiffResult(changes=sorted_changes)


def sort_by_severity(result: DiffResult, reverse: bool = False) -> DiffResult:
    """Return a new DiffResult with breaking changes listed before non-breaking.

    Args:
        result: The DiffResult to sort.
        reverse: If True, non-breaking changes are listed before breaking.
    """
    order = {ChangeType.BREAKING: 0, ChangeType.NON_BREAKING: 1}
    sorted_changes = sorted(
        result.changes, key=lambda c: order.get(c.change_type, 99), reverse=reverse
    )
    return DiffResult(changes=sorted_changes)


def sort_changes(
    result: DiffResult,
    by: str = "severity",
    reverse: bool = False,
) -> DiffResult:
    """Sort changes by the given strategy.

    Args:
        result: The DiffResult to sort.
        by: One of 'severity' or 'path'.
        reverse: If True, reverse the sort order.

    Returns:
        A new DiffResult with sorted changes.

    Raises:
        ValueError: If an unknown sort key is provided.
    """
    if by == "severity":
        return sort_by_severity(result, reverse=reverse)
    elif by == "path":
        return sort_by_path(result, reverse=reverse)
    else:
        raise ValueError(f"Unknown sort key: '{by}'. Use 'severity' or 'path'.")
