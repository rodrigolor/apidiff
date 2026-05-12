"""High-level transform helpers combining patch and merge operations."""

from __future__ import annotations

from typing import Any, Dict, List

from .differ import DiffResult, diff_specs
from .merger import merge_specs
from .patcher import apply_patch


def rebase_spec(
    old_spec: Dict[str, Any],
    new_spec: Dict[str, Any],
    base_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """Rebase *base_spec* by applying the delta between *old_spec* and *new_spec*.

    Computes the diff from *old_spec* to *new_spec* and applies all ADDED
    changes onto *base_spec*, then merges the result with *new_spec*'s
    top-level metadata (info, components, servers).

    Args:
        old_spec: The previous version of a spec (diff source).
        new_spec: The updated version of a spec (diff target).
        base_spec: The spec to rebase.

    Returns:
        A new spec dict representing the rebased result.
    """
    delta: DiffResult = diff_specs(old_spec, new_spec)
    patched = apply_patch(base_spec, delta)

    # Carry over top-level metadata from new_spec (non-paths keys).
    metadata_overlay: Dict[str, Any] = {
        k: v for k, v in new_spec.items() if k != "paths"
    }
    return merge_specs(patched, metadata_overlay, allow_version_mismatch=True)


def collect_breaking_paths(diff: DiffResult) -> List[str]:
    """Return a sorted list of unique paths that have at least one breaking change.

    Args:
        diff: A :class:`~apidiff.differ.DiffResult`.

    Returns:
        Sorted list of path strings.
    """
    from .differ import ChangeType  # local import to avoid circularity

    breaking_paths = {
        change.path
        for change in diff.changes
        if change.change_type == ChangeType.REMOVED and change.path
    }
    return sorted(breaking_paths)
