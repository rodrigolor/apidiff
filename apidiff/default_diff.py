"""Detect changes in default values for parameters and schema properties."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DefaultChange:
    path: str
    method: str
    location: str  # e.g. "param:limit" or "requestBody:application/json:count"
    old_default: Any
    new_default: Any

    def __str__(self) -> str:
        return (
            f"[{self.method.upper()} {self.path}] "
            f"{self.location}: default changed "
            f"{self.old_default!r} -> {self.new_default!r}"
        )

    def is_breaking(self) -> bool:
        """A default value change is considered non-breaking but noteworthy."""
        return False


@dataclass
class DefaultDiffResult:
    changes: list[DefaultChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.changes)

    def total(self) -> int:
        return len(self.changes)


def _diff_schema_defaults(
    path: str,
    method: str,
    location_prefix: str,
    base_schema: dict,
    head_schema: dict,
    result: DefaultDiffResult,
) -> None:
    base_default = base_schema.get("default")
    head_default = head_schema.get("default")
    if base_default != head_default and not (base_default is None and head_default is None):
        if base_default is not None or head_default is not None:
            result.changes.append(
                DefaultChange(
                    path=path,
                    method=method,
                    location=location_prefix,
                    old_default=base_default,
                    new_default=head_default,
                )
            )


def diff_defaults(base_spec: dict, head_spec: dict) -> DefaultDiffResult:
    result = DefaultDiffResult()
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})

    for path, base_item in base_paths.items():
        head_item = head_paths.get(path, {})
        for method, base_op in base_item.items():
            if method not in ("get", "post", "put", "patch", "delete", "options", "head"):
                continue
            head_op = head_item.get(method, {})

            # Check parameters
            base_params = {p["name"]: p for p in base_op.get("parameters", []) if "name" in p}
            head_params = {p["name"]: p for p in head_op.get("parameters", []) if "name" in p}
            for name, base_param in base_params.items():
                head_param = head_params.get(name, {})
                base_schema = base_param.get("schema", {})
                head_schema = head_param.get("schema", {})
                _diff_schema_defaults(
                    path, method, f"param:{name}", base_schema, head_schema, result
                )

            # Check requestBody media types
            base_body = base_op.get("requestBody", {}).get("content", {})
            head_body = head_op.get("requestBody", {}).get("content", {})
            for media_type, base_media in base_body.items():
                head_media = head_body.get(media_type, {})
                base_schema = base_media.get("schema", {})
                head_schema = head_media.get("schema", {})
                _diff_schema_defaults(
                    path, method, f"requestBody:{media_type}", base_schema, head_schema, result
                )

    return result
