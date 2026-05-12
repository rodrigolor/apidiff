"""Apply a diff result as a patch to produce an updated OpenAPI spec."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from .differ import ChangeType, DiffResult


class PatchError(Exception):
    """Raised when a patch cannot be applied."""


def _set_nested(spec: Dict[str, Any], path: str, method: str, key: str, value: Any) -> None:
    """Set a nested value inside the spec paths structure."""
    spec.setdefault("paths", {}).setdefault(path, {}).setdefault(method, {})[key] = value


def _remove_nested(spec: Dict[str, Any], path: str, method: str | None) -> None:
    """Remove a path or method from the spec."""
    paths = spec.get("paths", {})
    if path not in paths:
        return
    if method is None:
        del paths[path]
    else:
        paths[path].pop(method, None)
        if not paths[path]:
            del paths[path]


def apply_patch(base_spec: Dict[str, Any], diff: DiffResult) -> Dict[str, Any]:
    """Return a new spec with all non-breaking additions from *diff* applied.

    Only ADDED changes are applied; breaking removals are intentionally skipped
    so callers can choose how to handle them.

    Args:
        base_spec: The original OpenAPI spec dict.
        diff: A :class:`~apidiff.differ.DiffResult` produced by comparing two specs.

    Returns:
        A deep copy of *base_spec* with additions merged in.

    Raises:
        PatchError: If the spec structure is missing required keys.
    """
    if "paths" not in base_spec and any(c.path for c in diff.changes):
        raise PatchError("base_spec is missing 'paths' key")

    patched = deepcopy(base_spec)

    for change in diff.changes:
        if change.change_type == ChangeType.ADDED:
            if change.method:
                _set_nested(
                    patched,
                    change.path,
                    change.method.lower(),
                    "description",
                    change.description,
                )
            else:
                patched.setdefault("paths", {})[change.path] = {}

    return patched
