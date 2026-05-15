"""Diff writeOnly property changes across request/response schemas."""

from dataclasses import dataclass
from typing import List, Optional

from apidiff.differ import DiffResult


@dataclass
class WriteOnlyChange:
    path: str
    method: str
    field: str
    location: str  # 'request' or 'response'
    status_code: Optional[str]
    old_value: Optional[bool]
    new_value: Optional[bool]

    def __str__(self) -> str:
        loc = self.location
        if self.status_code:
            loc = f"{loc} [{self.status_code}]"
        old = self.old_value
        new = self.new_value
        return (
            f"{self.method.upper()} {self.path} — field '{self.field}' "
            f"writeOnly changed {old!r} -> {new!r} in {loc}"
        )

    def is_breaking(self) -> bool:
        # Making a field writeOnly in a response is breaking (clients lose read access)
        if self.location == "response" and not self.old_value and self.new_value:
            return True
        # Removing writeOnly from a request field is breaking (server may reject reads)
        if self.location == "request" and self.old_value and not self.new_value:
            return True
        return False


@dataclass
class WriteOnlyDiffResult:
    changes: List[WriteOnlyChange]

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    def total(self) -> int:
        return len(self.changes)

    def breaking_changes(self) -> List[WriteOnlyChange]:
        return [c for c in self.changes if c.is_breaking()]


def _scan_schema(schema: dict, prefix: str) -> List[tuple]:
    """Yield (field_path, writeOnly) pairs from a schema's properties."""
    results = []
    props = schema.get("properties", {})
    for name, field_schema in props.items():
        field_path = f"{prefix}.{name}" if prefix else name
        wo = field_schema.get("writeOnly")
        results.append((field_path, wo))
    return results


def diff_writeonly(base_spec: dict, head_spec: dict) -> WriteOnlyDiffResult:
    changes: List[WriteOnlyChange] = []
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})

    for path, base_methods in base_paths.items():
        head_methods = head_paths.get(path, {})
        for method, base_op in base_methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            head_op = head_methods.get(method, {})

            # Request body
            base_rb = base_op.get("requestBody", {}).get("content", {})
            head_rb = head_op.get("requestBody", {}).get("content", {})
            for media, base_media_obj in base_rb.items():
                head_media_obj = head_rb.get(media, {})
                base_schema = base_media_obj.get("schema", {})
                head_schema = head_media_obj.get("schema", {})
                for field, old_wo in _scan_schema(base_schema, ""):
                    new_wo = dict(_scan_schema(head_schema, "")).get(field)
                    if old_wo != new_wo:
                        changes.append(WriteOnlyChange(
                            path=path, method=method, field=field,
                            location="request", status_code=None,
                            old_value=old_wo, new_value=new_wo,
                        ))

            # Responses
            base_responses = base_op.get("responses", {})
            head_responses = head_op.get("responses", {})
            for status, base_resp in base_responses.items():
                head_resp = head_responses.get(status, {})
                for media, base_media_obj in base_resp.get("content", {}).items():
                    head_media_obj = head_resp.get("content", {}).get(media, {})
                    base_schema = base_media_obj.get("schema", {})
                    head_schema = head_media_obj.get("schema", {})
                    for field, old_wo in _scan_schema(base_schema, ""):
                        new_wo = dict(_scan_schema(head_schema, "")).get(field)
                        if old_wo != new_wo:
                            changes.append(WriteOnlyChange(
                                path=path, method=method, field=field,
                                location="response", status_code=str(status),
                                old_value=old_wo, new_value=new_wo,
                            ))

    return WriteOnlyDiffResult(changes=changes)
