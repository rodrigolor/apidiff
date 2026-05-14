"""Diff format/content-type declarations between two OpenAPI specs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FormatChange:
    path: str
    method: str
    location: str  # 'request' or 'response'
    status_code: Optional[str]  # None for request
    field: str  # 'format', 'type', etc.
    old_value: Optional[str]
    new_value: Optional[str]

    def __str__(self) -> str:
        loc = self.location
        if self.status_code:
            loc = f"{loc}[{self.status_code}]"
        direction = f"{self.old_value!r} -> {self.new_value!r}"
        return (
            f"[{self.method.upper()} {self.path}] {loc} "
            f"{self.field} changed: {direction}"
        )

    def is_breaking(self) -> bool:
        """A format change on a request or response body is potentially breaking."""
        # Removing a format or changing it is breaking; adding is non-breaking
        if self.old_value is not None and self.new_value is None:
            return True
        if self.old_value is not None and self.new_value != self.old_value:
            return True
        return False


@dataclass
class FormatDiffResult:
    changes: List[FormatChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    def total(self) -> int:
        return len(self.changes)


def _extract_schema_format(schema: dict) -> Optional[str]:
    if not isinstance(schema, dict):
        return None
    return schema.get("format") or schema.get("type")


def _diff_body_formats(
    path: str,
    method: str,
    base_op: dict,
    head_op: dict,
    changes: List[FormatChange],
) -> None:
    # Request body
    base_req = base_op.get("requestBody", {}).get("content", {})
    head_req = head_op.get("requestBody", {}).get("content", {})
    all_media = set(base_req) | set(head_req)
    for media in all_media:
        base_schema = base_req.get(media, {}).get("schema", {})
        head_schema = head_req.get(media, {}).get("schema", {})
        old_fmt = _extract_schema_format(base_schema)
        new_fmt = _extract_schema_format(head_schema)
        if old_fmt != new_fmt:
            changes.append(
                FormatChange(path, method, "request", None, "format", old_fmt, new_fmt)
            )

    # Responses
    base_resp = base_op.get("responses", {})
    head_resp = head_op.get("responses", {})
    all_codes = set(base_resp) | set(head_resp)
    for code in all_codes:
        base_content = base_resp.get(code, {}).get("content", {})
        head_content = head_resp.get(code, {}).get("content", {})
        all_media = set(base_content) | set(head_content)
        for media in all_media:
            base_schema = base_content.get(media, {}).get("schema", {})
            head_schema = head_content.get(media, {}).get("schema", {})
            old_fmt = _extract_schema_format(base_schema)
            new_fmt = _extract_schema_format(head_schema)
            if old_fmt != new_fmt:
                changes.append(
                    FormatChange(
                        path, method, "response", str(code), "format", old_fmt, new_fmt
                    )
                )


def diff_formats(base_spec: dict, head_spec: dict) -> FormatDiffResult:
    """Compare schema format/type fields across all operations."""
    changes: List[FormatChange] = []
    base_paths: Dict[str, dict] = base_spec.get("paths", {})
    head_paths: Dict[str, dict] = head_spec.get("paths", {})
    all_paths = set(base_paths) | set(head_paths)
    http_methods = {"get", "post", "put", "patch", "delete", "options", "head"}

    for path in all_paths:
        base_item = base_paths.get(path, {})
        head_item = head_paths.get(path, {})
        all_methods = (set(base_item) | set(head_item)) & http_methods
        for method in all_methods:
            base_op = base_item.get(method)
            head_op = head_item.get(method)
            if base_op is None or head_op is None:
                continue
            _diff_body_formats(path, method, base_op, head_op, changes)

    return FormatDiffResult(changes=changes)
