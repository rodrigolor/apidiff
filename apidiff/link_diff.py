"""Diff OpenAPI response links between two specs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LinkChange:
    path: str
    method: str
    status_code: str
    link_name: str
    change_kind: str  # 'added' | 'removed' | 'modified'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __str__(self) -> str:
        loc = f"{self.method.upper()} {self.path} [{self.status_code}] link '{self.link_name}'"
        if self.change_kind == "removed":
            return f"{loc}: link removed"
        if self.change_kind == "added":
            return f"{loc}: link added"
        return f"{loc}: operationRef changed from '{self.old_value}' to '{self.new_value}'"

    def is_breaking(self) -> bool:
        """Removing a link is considered non-breaking; modifications may matter to clients."""
        return self.change_kind == "removed"


@dataclass
class LinkDiffResult:
    changes: List[LinkChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.changes)

    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    def total(self) -> int:
        return len(self.changes)


def _get_links(spec: dict, path: str, method: str, status_code: str) -> Dict[str, dict]:
    try:
        return (
            spec.get("paths", {})
            .get(path, {})
            .get(method, {})
            .get("responses", {})
            .get(status_code, {})
            .get("links", {})
        )
    except AttributeError:
        return {}


def diff_links(base_spec: dict, head_spec: dict) -> LinkDiffResult:
    changes: List[LinkChange] = []
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})
    all_paths = set(base_paths) | set(head_paths)

    for path in sorted(all_paths):
        base_ops = base_paths.get(path, {})
        head_ops = head_paths.get(path, {})
        all_methods = set(base_ops) | set(head_ops)

        for method in sorted(all_methods):
            base_responses = base_ops.get(method, {}).get("responses", {})
            head_responses = head_ops.get(method, {}).get("responses", {})
            all_codes = set(base_responses) | set(head_responses)

            for code in sorted(all_codes):
                base_links = _get_links(base_spec, path, method, code)
                head_links = _get_links(head_spec, path, method, code)
                all_link_names = set(base_links) | set(head_links)

                for name in sorted(all_link_names):
                    if name not in base_links:
                        changes.append(LinkChange(path, method, code, name, "added"))
                    elif name not in head_links:
                        changes.append(LinkChange(path, method, code, name, "removed"))
                    else:
                        old_op = base_links[name].get("operationRef")
                        new_op = head_links[name].get("operationRef")
                        if old_op != new_op:
                            changes.append(
                                LinkChange(path, method, code, name, "modified", old_op, new_op)
                            )
    return LinkDiffResult(changes=changes)
