"""Detect parameter-level changes between two OpenAPI specs."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from apidiff.differ import Change, ChangeType, DiffResult


@dataclass
class ParamChange:
    """Represents a change to a single parameter."""
    path: str
    method: str
    param_name: str
    change_type: ChangeType
    detail: str = ""

    def __str__(self) -> str:
        loc = f"{self.method.upper()} {self.path} [{self.param_name}]"
        return f"{self.change_type.value}: {loc} — {self.detail}"


def _params_by_name(params: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Index a list of parameter objects by their name."""
    return {p["name"]: p for p in params if "name" in p}


def _is_required(param: Dict[str, Any]) -> bool:
    return bool(param.get("required", False))


def diff_parameters(
    path: str,
    method: str,
    base_params: List[Dict[str, Any]],
    head_params: List[Dict[str, Any]],
) -> List[ParamChange]:
    """Compare parameter lists for a single operation and return changes."""
    changes: List[ParamChange] = []
    base_map = _params_by_name(base_params)
    head_map = _params_by_name(head_params)

    for name, base_p in base_map.items():
        if name not in head_map:
            changes.append(ParamChange(
                path=path, method=method, param_name=name,
                change_type=ChangeType.BREAKING,
                detail="required parameter removed" if _is_required(base_p) else "optional parameter removed",
            ))
        else:
            head_p = head_map[name]
            if not _is_required(base_p) and _is_required(head_p):
                changes.append(ParamChange(
                    path=path, method=method, param_name=name,
                    change_type=ChangeType.BREAKING,
                    detail="parameter became required",
                ))
            elif _is_required(base_p) and not _is_required(head_p):
                changes.append(ParamChange(
                    path=path, method=method, param_name=name,
                    change_type=ChangeType.NON_BREAKING,
                    detail="parameter became optional",
                ))
            base_type = base_p.get("schema", {}).get("type")
            head_type = head_p.get("schema", {}).get("type")
            if base_type and head_type and base_type != head_type:
                changes.append(ParamChange(
                    path=path, method=method, param_name=name,
                    change_type=ChangeType.BREAKING,
                    detail=f"type changed from '{base_type}' to '{head_type}'",
                ))

    for name, head_p in head_map.items():
        if name not in base_map:
            ct = ChangeType.BREAKING if _is_required(head_p) else ChangeType.NON_BREAKING
            changes.append(ParamChange(
                path=path, method=method, param_name=name,
                change_type=ct,
                detail="new required parameter added" if _is_required(head_p) else "new optional parameter added",
            ))

    return changes


def extract_param_changes(
    base_spec: Dict[str, Any],
    head_spec: Dict[str, Any],
) -> List[ParamChange]:
    """Walk all shared paths/methods and collect parameter-level changes."""
    all_changes: List[ParamChange] = []
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})

    for path, base_item in base_paths.items():
        if path not in head_paths:
            continue
        head_item = head_paths[path]
        for method in ("get", "post", "put", "patch", "delete", "options", "head"):
            base_op = base_item.get(method)
            head_op = head_item.get(method)
            if base_op is None or head_op is None:
                continue
            base_params = base_op.get("parameters", [])
            head_params = head_op.get("parameters", [])
            all_changes.extend(diff_parameters(path, method, base_params, head_params))

    return all_changes
