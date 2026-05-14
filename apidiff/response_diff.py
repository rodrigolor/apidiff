"""Diff response schemas between two OpenAPI specs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apidiff.differ import Change, ChangeType, DiffResult


@dataclass
class ResponseChange:
    path: str
    method: str
    status_code: str
    field: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None

    def __str__(self) -> str:
        loc = f"{self.method.upper()} {self.path} [{self.status_code}] .{self.field}"
        if self.change_type == ChangeType.REMOVED:
            return f"{loc}: removed (was {self.old_value!r})"
        if self.change_type == ChangeType.ADDED:
            return f"{loc}: added {self.new_value!r}"
        return f"{loc}: changed from {self.old_value!r} to {self.new_value!r}"


def _get_responses(spec: dict, path: str, method: str) -> dict:
    return (
        spec.get("paths", {})
        .get(path, {})
        .get(method.lower(), {})
        .get("responses", {})
    )


def _diff_schema(path: str, method: str, status_code: str,
                 base_schema: dict, head_schema: dict) -> list[ResponseChange]:
    changes: list[ResponseChange] = []
    all_keys = set(base_schema) | set(head_schema)
    for key in all_keys:
        if key not in base_schema:
            changes.append(ResponseChange(path, method, status_code, key,
                                          ChangeType.ADDED, new_value=head_schema[key]))
        elif key not in head_schema:
            changes.append(ResponseChange(path, method, status_code, key,
                                          ChangeType.REMOVED, old_value=base_schema[key]))
        elif base_schema[key] != head_schema[key]:
            changes.append(ResponseChange(path, method, status_code, key,
                                          ChangeType.MODIFIED,
                                          old_value=base_schema[key],
                                          new_value=head_schema[key]))
    return changes


def diff_responses(base_spec: dict, head_spec: dict) -> list[ResponseChange]:
    """Return all response-level changes between base and head specs."""
    changes: list[ResponseChange] = []
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})
    all_paths = set(base_paths) | set(head_paths)

    for path in all_paths:
        base_methods = set(base_paths.get(path, {}).keys())
        head_methods = set(head_paths.get(path, {}).keys())
        for method in base_methods | head_methods:
            base_responses = _get_responses(base_spec, path, method)
            head_responses = _get_responses(head_spec, path, method)
            all_codes = set(base_responses) | set(head_responses)
            for code in all_codes:
                base_resp = base_responses.get(code, {})
                head_resp = head_responses.get(code, {})
                if code not in base_responses:
                    changes.append(ResponseChange(path, method, code, "<response>",
                                                  ChangeType.ADDED, new_value=head_resp))
                elif code not in head_responses:
                    changes.append(ResponseChange(path, method, code, "<response>",
                                                  ChangeType.REMOVED, old_value=base_resp))
                else:
                    base_schema = base_resp.get("schema", base_resp.get("content", {}))
                    head_schema = head_resp.get("schema", head_resp.get("content", {}))
                    if isinstance(base_schema, dict) and isinstance(head_schema, dict):
                        changes.extend(_diff_schema(path, method, code,
                                                    base_schema, head_schema))
    return changes


def is_breaking_response_change(rc: ResponseChange) -> bool:
    """A response change is breaking if a previously existing response code is removed."""
    return rc.change_type == ChangeType.REMOVED and rc.field == "<response>"
