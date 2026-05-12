"""Core diffing logic for comparing two OpenAPI specs."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeType(str, Enum):
    BREAKING = "breaking"
    NON_BREAKING = "non_breaking"
    INFO = "info"


@dataclass
class Change:
    change_type: ChangeType
    path: str
    message: str
    old_value: Any = None
    new_value: Any = None

    def __str__(self) -> str:
        prefix = {
            ChangeType.BREAKING: "[BREAKING]",
            ChangeType.NON_BREAKING: "[non-breaking]",
            ChangeType.INFO: "[info]",
        }[self.change_type]
        return f"{prefix} {self.path}: {self.message}"


@dataclass
class DiffResult:
    changes: list[Change] = field(default_factory=list)

    @property
    def breaking(self) -> list[Change]:
        return [c for c in self.changes if c.change_type == ChangeType.BREAKING]

    @property
    def non_breaking(self) -> list[Change]:
        return [c for c in self.changes if c.change_type == ChangeType.NON_BREAKING]

    @property
    def has_breaking_changes(self) -> bool:
        return len(self.breaking) > 0


def diff_specs(old_spec: dict, new_spec: dict) -> DiffResult:
    """Compare two OpenAPI spec dicts and return a DiffResult."""
    result = DiffResult()
    _diff_paths(old_spec, new_spec, result)
    _diff_info(old_spec, new_spec, result)
    return result


def _diff_info(old_spec: dict, new_spec: dict, result: DiffResult) -> None:
    old_version = old_spec.get("info", {}).get("version", "")
    new_version = new_spec.get("info", {}).get("version", "")
    if old_version != new_version:
        result.changes.append(Change(
            change_type=ChangeType.INFO,
            path="info.version",
            message=f"version changed from '{old_version}' to '{new_version}'",
            old_value=old_version,
            new_value=new_version,
        ))


def _diff_paths(old_spec: dict, new_spec: dict, result: DiffResult) -> None:
    old_paths = old_spec.get("paths", {})
    new_paths = new_spec.get("paths", {})

    for path, old_item in old_paths.items():
        if path not in new_paths:
            result.changes.append(Change(
                change_type=ChangeType.BREAKING,
                path=path,
                message="endpoint removed",
                old_value=list(old_item.keys()),
            ))
            continue
        _diff_path_item(path, old_item, new_paths[path], result)

    for path, new_item in new_paths.items():
        if path not in old_paths:
            result.changes.append(Change(
                change_type=ChangeType.NON_BREAKING,
                path=path,
                message="endpoint added",
                new_value=list(new_item.keys()),
            ))


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


def _diff_path_item(path: str, old_item: dict, new_item: dict, result: DiffResult) -> None:
    old_methods = {m for m in old_item if m.lower() in HTTP_METHODS}
    new_methods = {m for m in new_item if m.lower() in HTTP_METHODS}

    for method in old_methods - new_methods:
        result.changes.append(Change(
            change_type=ChangeType.BREAKING,
            path=f"{path}.{method}",
            message="operation removed",
        ))

    for method in new_methods - old_methods:
        result.changes.append(Change(
            change_type=ChangeType.NON_BREAKING,
            path=f"{path}.{method}",
            message="operation added",
        ))

    for method in old_methods & new_methods:
        _diff_operation(path, method, old_item[method], new_item[method], result)


def _diff_operation(path: str, method: str, old_op: dict, new_op: dict, result: DiffResult) -> None:
    op_path = f"{path}.{method}"
    _diff_parameters(op_path, old_op.get("parameters", []), new_op.get("parameters", []), result)
    _diff_responses(op_path, old_op.get("responses", {}), new_op.get("responses", {}), result)


def _diff_parameters(op_path: str, old_params: list, new_params: list, result: DiffResult) -> None:
    def key(p: dict) -> str:
        return f"{p.get('in', '')}:{p.get('name', '')}"

    old_map = {key(p): p for p in old_params}
    new_map = {key(p): p for p in new_params}

    for k, old_p in old_map.items():
        if k not in new_map:
            result.changes.append(Change(
                change_type=ChangeType.BREAKING,
                path=f"{op_path}.parameters.{k}",
                message="required parameter removed",
                old_value=old_p,
            ))
        else:
            new_p = new_map[k]
            if not old_p.get("required") and new_p.get("required"):
                result.changes.append(Change(
                    change_type=ChangeType.BREAKING,
                    path=f"{op_path}.parameters.{k}",
                    message="parameter became required",
                ))

    for k, new_p in new_map.items():
        if k not in old_map:
            result.changes.append(Change(
                change_type=ChangeType.NON_BREAKING,
                path=f"{op_path}.parameters.{k}",
                message="parameter added",
                new_value=new_p,
            ))


def _diff_responses(op_path: str, old_responses: dict, new_responses: dict, result: DiffResult) -> None:
    for status, _ in old_responses.items():
        if status not in new_responses:
            result.changes.append(Change(
                change_type=ChangeType.BREAKING,
                path=f"{op_path}.responses.{status}",
                message="response status code removed",
            ))

    for status, _ in new_responses.items():
        if status not in old_responses:
            result.changes.append(Change(
                change_type=ChangeType.NON_BREAKING,
                path=f"{op_path}.responses.{status}",
                message="response status code added",
            ))
