"""Schema-level diffing for OpenAPI request body and component schemas.

Compares JSON Schema objects between two spec versions and identifies
breaking vs non-breaking changes at the field/type level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from apidiff.differ import ChangeType


@dataclass
class SchemaChange:
    """Represents a single change within a JSON Schema object."""

    field_path: str  # dot-separated path, e.g. "properties.name.type"
    change_type: ChangeType
    base_value: Any
    head_value: Any
    breaking: bool

    def __str__(self) -> str:
        direction = "breaking" if self.breaking else "non-breaking"
        return (
            f"[{direction}] {self.change_type.value} at '{self.field_path}': "
            f"{self.base_value!r} -> {self.head_value!r}"
        )


@dataclass
class SchemaReport:
    """Aggregated schema diff report for a single schema comparison."""

    schema_name: str
    changes: List[SchemaChange] = field(default_factory=list)

    @property
    def has_breaking(self) -> bool:
        return any(c.breaking for c in self.changes)

    @property
    def breaking_changes(self) -> List[SchemaChange]:
        return [c for c in self.changes if c.breaking]

    @property
    def non_breaking_changes(self) -> List[SchemaChange]:
        return [c for c in self.changes if not c.breaking]


# Fields whose removal or narrowing is considered breaking.
_BREAKING_TYPE_CHANGES = {
    ("string", "integer"),
    ("string", "number"),
    ("string", "boolean"),
    ("integer", "string"),
    ("integer", "boolean"),
    ("number", "string"),
    ("number", "boolean"),
    ("boolean", "string"),
    ("boolean", "integer"),
    ("array", "object"),
    ("object", "array"),
}


def _is_type_change_breaking(base_type: str, head_type: str) -> bool:
    """Return True if changing from base_type to head_type is breaking."""
    return (str(base_type), str(head_type)) in _BREAKING_TYPE_CHANGES


def _diff_schema_object(
    base: Dict[str, Any],
    head: Dict[str, Any],
    prefix: str,
    changes: List[SchemaChange],
) -> None:
    """Recursively compare two schema dicts and append SchemaChange entries."""
    all_keys = set(base.keys()) | set(head.keys())

    for key in sorted(all_keys):
        path = f"{prefix}.{key}" if prefix else key
        base_val = base.get(key)
        head_val = head.get(key)

        if base_val is None:
            # Field added — generally non-breaking unless required
            changes.append(
                SchemaChange(
                    field_path=path,
                    change_type=ChangeType.ADDED,
                    base_value=None,
                    head_value=head_val,
                    breaking=False,
                )
            )
        elif head_val is None:
            # Field removed — breaking if it was a required property or type info
            is_breaking = key in ("type", "required", "properties")
            changes.append(
                SchemaChange(
                    field_path=path,
                    change_type=ChangeType.REMOVED,
                    base_value=base_val,
                    head_value=None,
                    breaking=is_breaking,
                )
            )
        elif isinstance(base_val, dict) and isinstance(head_val, dict):
            _diff_schema_object(base_val, head_val, path, changes)
        elif isinstance(base_val, list) and isinstance(head_val, list):
            if set(map(str, base_val)) != set(map(str, head_val)):
                # Treat required array changes as breaking when items are removed
                removed = set(map(str, base_val)) - set(map(str, head_val))
                changes.append(
                    SchemaChange(
                        field_path=path,
                        change_type=ChangeType.MODIFIED,
                        base_value=base_val,
                        head_value=head_val,
                        breaking=bool(removed) and key == "required",
                    )
                )
        elif base_val != head_val:
            breaking = False
            if key == "type":
                breaking = _is_type_change_breaking(str(base_val), str(head_val))
            elif key == "format":
                # Narrowing format (e.g. removing format) is non-breaking
                breaking = head_val is None and base_val is not None
            elif key in ("minimum", "minLength", "minItems"):
                # Increasing a minimum is breaking for consumers
                try:
                    breaking = float(head_val) > float(base_val)
                except (TypeError, ValueError):
                    breaking = False
            elif key in ("maximum", "maxLength", "maxItems"):
                # Decreasing a maximum is breaking for consumers
                try:
                    breaking = float(head_val) < float(base_val)
                except (TypeError, ValueError):
                    breaking = False

            changes.append(
                SchemaChange(
                    field_path=path,
                    change_type=ChangeType.MODIFIED,
                    base_value=base_val,
                    head_value=head_val,
                    breaking=breaking,
                )
            )


def diff_schema(
    schema_name: str,
    base_schema: Optional[Dict[str, Any]],
    head_schema: Optional[Dict[str, Any]],
) -> SchemaReport:
    """Diff two JSON Schema objects and return a SchemaReport.

    Args:
        schema_name: Logical name for the schema (used in report).
        base_schema:  Schema from the base/old spec.
        head_schema:  Schema from the head/new spec.

    Returns:
        SchemaReport with all detected changes.
    """
    report = SchemaReport(schema_name=schema_name)

    if base_schema is None and head_schema is None:
        return report

    if base_schema is None:
        report.changes.append(
            SchemaChange(
                field_path="(root)",
                change_type=ChangeType.ADDED,
                base_value=None,
                head_value=head_schema,
                breaking=False,
            )
        )
        return report

    if head_schema is None:
        report.changes.append(
            SchemaChange(
                field_path="(root)",
                change_type=ChangeType.REMOVED,
                base_value=base_schema,
                head_value=None,
                breaking=True,
            )
        )
        return report

    _diff_schema_object(base_schema, head_schema, "", report.changes)
    return report


def diff_component_schemas(
    base_spec: Dict[str, Any],
    head_spec: Dict[str, Any],
) -> List[SchemaReport]:
    """Compare all schemas defined under components/schemas in two specs.

    Args:
        base_spec: Parsed base OpenAPI spec dict.
        head_spec: Parsed head OpenAPI spec dict.

    Returns:
        List of SchemaReport, one per schema name found in either spec.
    """
    base_schemas: Dict[str, Any] = (
        base_spec.get("components", {}).get("schemas", {})
    )
    head_schemas: Dict[str, Any] = (
        head_spec.get("components", {}).get("schemas", {})
    )

    all_names = sorted(set(base_schemas.keys()) | set(head_schemas.keys()))
    reports = []
    for name in all_names:
        report = diff_schema(
            schema_name=name,
            base_schema=base_schemas.get(name),
            head_schema=head_schemas.get(name),
        )
        if report.changes:  # Only include schemas that actually changed
            reports.append(report)
    return reports
