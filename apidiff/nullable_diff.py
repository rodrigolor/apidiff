"""Detect changes to `nullable` flags on schema fields across two OpenAPI specs.

A field becoming *not* nullable (nullable removed or set to False) when it was
previously nullable is a **breaking** change for consumers that may send or
receive null values.  The reverse (adding nullable) is non-breaking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional


@dataclass
class NullableChange:
    """Represents a change in the nullable flag for a single schema field."""

    path: str
    method: str
    location: str          # e.g. "request", "response:200"
    field_path: str        # JSON-pointer-style path within the schema, e.g. "/properties/name"
    was_nullable: bool
    is_nullable: bool

    def __str__(self) -> str:  # noqa: D105
        direction = "nullable → non-nullable" if self.is_breaking() else "non-nullable → nullable"
        return (
            f"{self.method.upper()} {self.path} "
            f"[{self.location}] {self.field_path}: {direction}"
        )

    def is_breaking(self) -> bool:
        """Return True when a previously nullable field becomes non-nullable."""
        return self.was_nullable and not self.is_nullable


@dataclass
class NullableDiffResult:
    """Collection of nullable changes found between two specs."""

    changes: List[NullableChange] = field(default_factory=list)

    def has_changes(self) -> bool:  # noqa: D102
        return bool(self.changes)

    def has_breaking(self) -> bool:  # noqa: D102
        return any(c.is_breaking() for c in self.changes)

    def breaking_changes(self) -> List[NullableChange]:  # noqa: D102
        return [c for c in self.changes if c.is_breaking()]

    def total(self) -> int:  # noqa: D102
        return len(self.changes)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _nullable_fields(schema: dict, prefix: str = "") -> Iterator[tuple[str, bool]]:
    """Recursively yield (field_path, nullable_flag) for every property in *schema*."""
    if not isinstance(schema, dict):
        return

    # Check the schema itself
    if "nullable" in schema:
        yield prefix or "/", bool(schema["nullable"])

    for prop_name, prop_schema in schema.get("properties", {}).items():
        child_prefix = f"{prefix}/properties/{prop_name}"
        yield from _nullable_fields(prop_schema, child_prefix)

    # Handle array items
    if "items" in schema:
        yield from _nullable_fields(schema["items"], f"{prefix}/items")


def _get_schema(operation: dict, location: str) -> Optional[dict]:
    """Extract a schema dict from an operation for the given *location* string.

    *location* is either ``"request"`` or ``"response:<status_code>"``.
    Returns ``None`` when no schema can be found.
    """
    if location == "request":
        rb = operation.get("requestBody", {})
        for media in rb.get("content", {}).values():
            schema = media.get("schema")
            if schema:
                return schema
        return None

    if location.startswith("response:"):
        status = location.split(":", 1)[1]
        resp = operation.get("responses", {}).get(status, {})
        for media in resp.get("content", {}).values():
            schema = media.get("schema")
            if schema:
                return schema
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def diff_nullable(base_spec: dict, head_spec: dict) -> NullableDiffResult:
    """Compare nullable flags across all operations in *base_spec* and *head_spec*.

    Only paths/methods present in **both** specs are examined; added or removed
    endpoints are handled by the core :mod:`apidiff.differ` module.
    """
    result = NullableDiffResult()

    http_methods = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

    base_paths: dict = base_spec.get("paths", {})
    head_paths: dict = head_spec.get("paths", {})

    for path, base_item in base_paths.items():
        head_item = head_paths.get(path)
        if not head_item:
            continue

        for method in http_methods:
            base_op = base_item.get(method)
            head_op = head_item.get(method)
            if not base_op or not head_op:
                continue

            # Build list of locations to inspect
            locations = ["request"]
            for status in set(
                list(base_op.get("responses", {}).keys())
                + list(head_op.get("responses", {}).keys())
            ):
                locations.append(f"response:{status}")

            for loc in locations:
                base_schema = _get_schema(base_op, loc)
                head_schema = _get_schema(head_op, loc)
                if base_schema is None or head_schema is None:
                    continue

                base_nullable = dict(_nullable_fields(base_schema))
                head_nullable = dict(_nullable_fields(head_schema))

                all_field_paths = set(base_nullable) | set(head_nullable)
                for fp in all_field_paths:
                    was = base_nullable.get(fp, False)
                    now = head_nullable.get(fp, False)
                    if was != now:
                        result.changes.append(
                            NullableChange(
                                path=path,
                                method=method,
                                location=loc,
                                field_path=fp,
                                was_nullable=was,
                                is_nullable=now,
                            )
                        )

    return result
