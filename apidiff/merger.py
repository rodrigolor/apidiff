"""Merge two OpenAPI specs, preferring values from the overlay spec."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


class MergeError(Exception):
    """Raised when specs cannot be merged."""


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *overlay* into *base*, returning a new dict."""
    result = deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def merge_specs(
    base_spec: Dict[str, Any],
    overlay_spec: Dict[str, Any],
    *,
    allow_version_mismatch: bool = False,
) -> Dict[str, Any]:
    """Merge two OpenAPI spec dicts.

    Values in *overlay_spec* take precedence over *base_spec*.
    Path-level and operation-level entries are deep-merged.

    Args:
        base_spec: The base OpenAPI spec.
        overlay_spec: The spec whose values take priority.
        allow_version_mismatch: When ``False`` (default), raises :class:`MergeError`
            if the ``openapi`` version strings differ.

    Returns:
        A new merged spec dict.

    Raises:
        MergeError: If version strings conflict and *allow_version_mismatch* is False.
    """
    base_version = base_spec.get("openapi", "")
    overlay_version = overlay_spec.get("openapi", "")

    if not allow_version_mismatch and base_version and overlay_version:
        if base_version != overlay_version:
            raise MergeError(
                f"OpenAPI version mismatch: {base_version!r} vs {overlay_version!r}. "
                "Pass allow_version_mismatch=True to suppress."
            )

    return _deep_merge(base_spec, overlay_spec)
