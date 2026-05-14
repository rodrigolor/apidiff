"""Diff OpenAPI vendor extension fields (x-*) between two specs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExtensionChange:
    """Represents a change in a vendor extension field."""

    key: str
    path: Optional[str]
    method: Optional[str]
    old_value: Any
    new_value: Any

    def __str__(self) -> str:
        location = ""
        if self.path:
            location = self.path
            if self.method:
                location = f"{self.method.upper()} {self.path}"
        prefix = f"[{location}] " if location else ""
        if self.old_value is None:
            return f"{prefix}{self.key} added: {self.new_value!r}"
        if self.new_value is None:
            return f"{prefix}{self.key} removed (was {self.old_value!r})"
        return f"{prefix}{self.key} changed: {self.old_value!r} -> {self.new_value!r}"


@dataclass
class ExtensionDiffResult:
    """Aggregated result of all extension diffs."""

    changes: List[ExtensionChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    @property
    def total(self) -> int:
        return len(self.changes)


def _diff_extensions(
    old: Dict[str, Any],
    new: Dict[str, Any],
    path: Optional[str] = None,
    method: Optional[str] = None,
) -> List[ExtensionChange]:
    """Compare extension keys (x-*) between two dicts."""
    changes: List[ExtensionChange] = []
    old_ext = {k: v for k, v in old.items() if k.startswith("x-")}
    new_ext = {k: v for k, v in new.items() if k.startswith("x-")}
    all_keys = set(old_ext) | set(new_ext)
    for key in sorted(all_keys):
        old_val = old_ext.get(key)
        new_val = new_ext.get(key)
        if old_val != new_val:
            changes.append(ExtensionChange(key=key, path=path, method=method,
                                           old_value=old_val, new_value=new_val))
    return changes


def diff_extensions(base: Dict[str, Any], head: Dict[str, Any]) -> ExtensionDiffResult:
    """Diff vendor extensions at the top level and per operation."""
    changes: List[ExtensionChange] = []

    # Top-level extensions
    changes.extend(_diff_extensions(base, head))

    base_paths: Dict[str, Any] = base.get("paths", {})
    head_paths: Dict[str, Any] = head.get("paths", {})
    all_paths = set(base_paths) | set(head_paths)

    for path in sorted(all_paths):
        base_path_item = base_paths.get(path, {})
        head_path_item = head_paths.get(path, {})

        # Path-level extensions
        changes.extend(_diff_extensions(base_path_item, head_path_item, path=path))

        http_methods = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
        all_methods = (set(base_path_item) | set(head_path_item)) & http_methods

        for method in sorted(all_methods):
            base_op = base_path_item.get(method, {})
            head_op = head_path_item.get(method, {})
            changes.extend(_diff_extensions(base_op, head_op, path=path, method=method))

    return ExtensionDiffResult(changes=changes)
