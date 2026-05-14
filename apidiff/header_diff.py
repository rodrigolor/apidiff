"""Diff response/request headers between two OpenAPI specs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from apidiff.differ import ChangeType


@dataclass
class HeaderChange:
    path: str
    method: str
    location: str  # 'request' or 'response'
    status_code: Optional[str]  # None for request headers
    header_name: str
    change_type: ChangeType
    detail: str

    def __str__(self) -> str:
        loc = (
            f"{self.location}({self.status_code})"
            if self.status_code
            else self.location
        )
        return (
            f"[{self.change_type.value}] {self.method.upper()} {self.path} "
            f"{loc} header '{self.header_name}': {self.detail}"
        )

    @property
    def is_breaking(self) -> bool:
        return self.change_type == ChangeType.BREAKING


def _extract_response_headers(
    spec: dict, path: str, method: str
) -> Dict[str, Dict[str, dict]]:
    """Return {status_code: {header_name: header_obj}} for a given operation."""
    result: Dict[str, Dict[str, dict]] = {}
    operation = spec.get("paths", {}).get(path, {}).get(method, {})
    for status_code, response_obj in operation.get("responses", {}).items():
        headers = response_obj.get("headers", {})
        if headers:
            result[str(status_code)] = headers
    return result


def _extract_param_headers(spec: dict, path: str, method: str) -> Dict[str, dict]:
    """Return {header_name: param_obj} for header-type parameters."""
    operation = spec.get("paths", {}).get(path, {}).get(method, {})
    params = operation.get("parameters", [])
    return {
        p["name"]: p
        for p in params
        if isinstance(p, dict) and p.get("in") == "header"
    }


def diff_headers(
    base_spec: dict,
    head_spec: dict,
    path: str,
    method: str,
) -> List[HeaderChange]:
    """Compare headers for a single operation between base and head specs."""
    changes: List[HeaderChange] = []

    # --- request (parameter) headers ---
    base_req = _extract_param_headers(base_spec, path, method)
    head_req = _extract_param_headers(head_spec, path, method)

    for name in base_req:
        if name not in head_req:
            changes.append(
                HeaderChange(path, method, "request", None, name,
                             ChangeType.BREAKING, "required header parameter removed")
            )
        else:
            base_required = base_req[name].get("required", False)
            head_required = head_req[name].get("required", False)
            if not base_required and head_required:
                changes.append(
                    HeaderChange(path, method, "request", None, name,
                                 ChangeType.BREAKING, "header parameter became required")
                )

    for name in head_req:
        if name not in base_req:
            changes.append(
                HeaderChange(path, method, "request", None, name,
                             ChangeType.NON_BREAKING, "new header parameter added")
            )

    # --- response headers ---
    base_resp = _extract_response_headers(base_spec, path, method)
    head_resp = _extract_response_headers(head_spec, path, method)

    all_codes = set(base_resp) | set(head_resp)
    for code in all_codes:
        base_headers = base_resp.get(code, {})
        head_headers = head_resp.get(code, {})
        for name in base_headers:
            if name not in head_headers:
                changes.append(
                    HeaderChange(path, method, "response", code, name,
                                 ChangeType.NON_BREAKING, "response header removed")
                )
        for name in head_headers:
            if name not in base_headers:
                changes.append(
                    HeaderChange(path, method, "response", code, name,
                                 ChangeType.NON_BREAKING, "response header added")
                )

    return changes
