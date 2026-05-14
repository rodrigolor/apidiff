"""Diff media types (content types) between two OpenAPI specs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MediaTypeChange:
    path: str
    method: str
    location: str  # 'request' or response status code e.g. '200'
    change_kind: str  # 'added', 'removed', 'schema_changed'
    media_type: str
    detail: Optional[str] = None

    def __str__(self) -> str:
        parts = [f"[{self.change_kind.upper()}]", self.media_type,
                 f"({self.location})", self.path, self.method.upper()]
        if self.detail:
            parts.append(f"- {self.detail}")
        return " ".join(parts)

    def is_breaking(self) -> bool:
        """Removing a media type is breaking; adding is non-breaking."""
        return self.change_kind == "removed"


@dataclass
class MediaTypeDiffResult:
    changes: List[MediaTypeChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    def total(self) -> int:
        return len(self.changes)


def _extract_content(operation: dict) -> Dict[str, dict]:
    return operation.get("requestBody", {}).get("content", {})


def _extract_response_content(operation: dict) -> Dict[str, Dict[str, dict]]:
    responses = operation.get("responses", {})
    return {
        status: resp.get("content", {})
        for status, resp in responses.items()
        if isinstance(resp, dict)
    }


def diff_media_types(base_spec: dict, head_spec: dict) -> MediaTypeDiffResult:
    """Compare media types for all shared paths/methods."""
    changes: List[MediaTypeChange] = []
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})

    for path, base_item in base_paths.items():
        head_item = head_paths.get(path, {})
        for method in ("get", "post", "put", "patch", "delete", "options", "head"):
            base_op = base_item.get(method)
            head_op = head_item.get(method)
            if not base_op or not head_op:
                continue

            # Request body content
            base_req = _extract_content(base_op)
            head_req = _extract_content(head_op)
            for mt in set(base_req) | set(head_req):
                if mt in base_req and mt not in head_req:
                    changes.append(MediaTypeChange(path, method, "request", "removed", mt))
                elif mt not in base_req and mt in head_req:
                    changes.append(MediaTypeChange(path, method, "request", "added", mt))

            # Response content
            base_resp = _extract_response_content(base_op)
            head_resp = _extract_response_content(head_op)
            for status in set(base_resp) | set(head_resp):
                b_content = base_resp.get(status, {})
                h_content = head_resp.get(status, {})
                for mt in set(b_content) | set(h_content):
                    if mt in b_content and mt not in h_content:
                        changes.append(MediaTypeChange(path, method, status, "removed", mt))
                    elif mt not in b_content and mt in h_content:
                        changes.append(MediaTypeChange(path, method, status, "added", mt))

    return MediaTypeDiffResult(changes=changes)
