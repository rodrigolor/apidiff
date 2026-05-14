"""Detect changes in enum values across OpenAPI spec endpoints."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnumChange:
    path: str
    method: str
    location: str  # e.g. "param:status" or "response:200:body"
    added: list[Any] = field(default_factory=list)
    removed: list[Any] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"{self.method.upper()} {self.path} [{self.location}]"]
        if self.removed:
            parts.append(f"  removed values: {self.removed}")
        if self.added:
            parts.append(f"  added values: {self.added}")
        return "\n".join(parts)

    def is_breaking(self) -> bool:
        """Removing enum values is breaking; adding is non-breaking."""
        return len(self.removed) > 0


@dataclass
class EnumDiffResult:
    changes: list[EnumChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    def total(self) -> int:
        return len(self.changes)


def _extract_enums_from_schema(schema: dict) -> list[Any] | None:
    """Return enum list from a schema dict, or None if not present."""
    if not isinstance(schema, dict):
        return None
    return schema.get("enum")


def _diff_enum(base_enum: list, head_enum: list) -> tuple[list, list]:
    base_set = set(map(str, base_enum))
    head_set = set(map(str, head_enum))
    removed = [v for v in base_enum if str(v) not in head_set]
    added = [v for v in head_enum if str(v) not in base_set]
    return added, removed


def diff_enums(base_spec: dict, head_spec: dict) -> EnumDiffResult:
    """Compare enum values in parameters and request bodies across all paths."""
    result = EnumDiffResult()
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})

    for path, base_methods in base_paths.items():
        head_methods = head_paths.get(path, {})
        for method, base_op in base_methods.items():
            if not isinstance(base_op, dict):
                continue
            head_op = head_methods.get(method, {}) if isinstance(head_methods, dict) else {}

            # Check parameters
            base_params = {p["name"]: p for p in base_op.get("parameters", []) if "name" in p}
            head_params = {p["name"]: p for p in head_op.get("parameters", []) if "name" in p}
            for param_name, base_param in base_params.items():
                head_param = head_params.get(param_name, {})
                base_enum = _extract_enums_from_schema(base_param.get("schema", {}))
                head_enum = _extract_enums_from_schema(head_param.get("schema", {}))
                if base_enum is not None and head_enum is not None and base_enum != head_enum:
                    added, removed = _diff_enum(base_enum, head_enum)
                    if added or removed:
                        result.changes.append(EnumChange(
                            path=path, method=method,
                            location=f"param:{param_name}",
                            added=added, removed=removed,
                        ))

    return result
