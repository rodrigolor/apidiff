"""Detect changes to readOnly and writeOnly field markers in request/response schemas.

readOnly fields becoming writable (or vice versa) can be a breaking change
for clients that rely on those constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from apidiff.differ import DiffResult


@dataclass
class ReadOnlyChange:
    """Represents a change to a readOnly or writeOnly marker on a schema field."""

    path: str
    method: str
    field_path: str  # e.g. "requestBody.content.application/json.schema.properties.id"
    marker: str      # "readOnly" or "writeOnly"
    old_value: bool
    new_value: bool
    in_response: bool  # True if the change is inside a response schema

    def __str__(self) -> str:
        direction = "response" if self.in_response else "request"
        return (
            f"[{self.method.upper()} {self.path}] {direction} field "
            f"'{self.field_path}': {self.marker} changed "
            f"{self.old_value} -> {self.new_value}"
        )

    def is_breaking(self) -> bool:
        """Determine whether this marker change is breaking.

        Breaking cases:
        - readOnly gains True in a request schema (client can no longer send it)
        - readOnly loses True in a response schema (server may stop returning it)
        - writeOnly gains True in a response schema (server stops returning it)
        - writeOnly loses True in a request schema (client can no longer send it)
        """
        if self.marker == "readOnly":
            if not self.in_response and self.new_value is True:
                return True  # request field became read-only
            if self.in_response and self.old_value is True and self.new_value is False:
                return True  # response field was read-only, now it isn't
        if self.marker == "writeOnly":
            if self.in_response and self.new_value is True:
                return True  # response field became write-only
            if not self.in_response and self.old_value is True and self.new_value is False:
                return True  # request field was write-only, now it isn't
        return False


@dataclass
class ReadOnlyDiffResult:
    """Aggregated result of readOnly/writeOnly marker diffing."""

    changes: List[ReadOnlyChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.changes)

    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    def total(self) -> int:
        return len(self.changes)


def _walk_properties(
    base_props: dict,
    head_props: dict,
    prefix: str,
    path: str,
    method: str,
    in_response: bool,
    results: List[ReadOnlyChange],
) -> None:
    """Recursively walk schema properties and detect marker changes."""
    all_keys = set(base_props) | set(head_props)
    for prop_name in all_keys:
        full_path = f"{prefix}.{prop_name}" if prefix else prop_name
        base_prop = base_props.get(prop_name, {})
        head_prop = head_props.get(prop_name, {})

        for marker in ("readOnly", "writeOnly"):
            old_val = bool(base_prop.get(marker, False))
            new_val = bool(head_prop.get(marker, False))
            if old_val != new_val:
                results.append(
                    ReadOnlyChange(
                        path=path,
                        method=method,
                        field_path=full_path,
                        marker=marker,
                        old_value=old_val,
                        new_value=new_val,
                        in_response=in_response,
                    )
                )

        # Recurse into nested objects
        base_nested = base_prop.get("properties", {})
        head_nested = head_prop.get("properties", {})
        if base_nested or head_nested:
            _walk_properties(
                base_nested, head_nested, full_path, path, method, in_response, results
            )


def _schema_from_request_body(operation: dict) -> Optional[dict]:
    """Extract the first JSON schema from a requestBody, if present."""
    content = operation.get("requestBody", {}).get("content", {})
    for media_type_obj in content.values():
        schema = media_type_obj.get("schema")
        if schema:
            return schema
    return None


def _schemas_from_responses(operation: dict) -> List[dict]:
    """Extract all JSON schemas from operation responses."""
    schemas = []
    for response_obj in operation.get("responses", {}).values():
        content = response_obj.get("content", {}) if isinstance(response_obj, dict) else {}
        for media_type_obj in content.values():
            schema = media_type_obj.get("schema")
            if schema:
                schemas.append(schema)
    return schemas


def diff_readonly(
    base_spec: dict,
    head_spec: dict,
    diff_result: Optional[DiffResult] = None,  # noqa: ARG001  (reserved for future use)
) -> ReadOnlyDiffResult:
    """Diff readOnly/writeOnly markers across all shared endpoints.

    Args:
        base_spec: The original OpenAPI spec dict.
        head_spec: The updated OpenAPI spec dict.
        diff_result: Optional pre-computed DiffResult (unused, kept for API parity).

    Returns:
        A ReadOnlyDiffResult containing all detected marker changes.
    """
    result = ReadOnlyDiffResult()
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})

    for path, base_path_item in base_paths.items():
        head_path_item = head_paths.get(path)
        if not head_path_item:
            continue  # endpoint removed — handled by the main differ

        http_methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
        for method in http_methods:
            base_op = base_path_item.get(method)
            head_op = head_path_item.get(method)
            if not base_op or not head_op:
                continue

            # --- Request body ---
            base_req_schema = _schema_from_request_body(base_op) or {}
            head_req_schema = _schema_from_request_body(head_op) or {}
            base_req_props = base_req_schema.get("properties", {})
            head_req_props = head_req_schema.get("properties", {})
            if base_req_props or head_req_props:
                _walk_properties(
                    base_req_props, head_req_props, "", path, method, False, result.changes
                )

            # --- Response bodies ---
            base_resp_schemas = _schemas_from_responses(base_op)
            head_resp_schemas = _schemas_from_responses(head_op)
            for base_schema, head_schema in zip(base_resp_schemas, head_resp_schemas):
                base_props = base_schema.get("properties", {})
                head_props = head_schema.get("properties", {})
                if base_props or head_props:
                    _walk_properties(
                        base_props, head_props, "", path, method, True, result.changes
                    )

    return result
