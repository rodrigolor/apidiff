"""Diff security scheme changes between two OpenAPI specs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SecurityChange:
    scheme_name: str
    change_type: str  # 'added', 'removed', 'modified'
    field: Optional[str] = None
    old_value: Any = None
    new_value: Any = None

    def __str__(self) -> str:
        if self.change_type == "removed":
            return f"Security scheme '{self.scheme_name}' removed (breaking)"
        if self.change_type == "added":
            return f"Security scheme '{self.scheme_name}' added"
        return (
            f"Security scheme '{self.scheme_name}' field '{self.field}' "
            f"changed: {self.old_value!r} -> {self.new_value!r}"
        )

    def is_breaking(self) -> bool:
        if self.change_type == "removed":
            return True
        if self.change_type == "modified" and self.field in ("type", "scheme", "bearerFormat"):
            return True
        return False


@dataclass
class SecurityDiffResult:
    changes: List[SecurityChange] = field(default_factory=list)

    @property
    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)


def _get_security_schemes(spec: Dict[str, Any]) -> Dict[str, Any]:
    return spec.get("components", {}).get("securitySchemes", {})


def _diff_scheme(
    name: str, base: Dict[str, Any], head: Dict[str, Any]
) -> List[SecurityChange]:
    changes: List[SecurityChange] = []
    all_keys = set(base) | set(head)
    for key in all_keys:
        bv = base.get(key)
        hv = head.get(key)
        if bv != hv:
            changes.append(
                SecurityChange(
                    scheme_name=name,
                    change_type="modified",
                    field=key,
                    old_value=bv,
                    new_value=hv,
                )
            )
    return changes


def diff_security(
    base_spec: Dict[str, Any], head_spec: Dict[str, Any]
) -> SecurityDiffResult:
    base_schemes = _get_security_schemes(base_spec)
    head_schemes = _get_security_schemes(head_spec)

    changes: List[SecurityChange] = []

    for name in base_schemes:
        if name not in head_schemes:
            changes.append(SecurityChange(scheme_name=name, change_type="removed"))
        else:
            changes.extend(_diff_scheme(name, base_schemes[name], head_schemes[name]))

    for name in head_schemes:
        if name not in base_schemes:
            changes.append(SecurityChange(scheme_name=name, change_type="added"))

    return SecurityDiffResult(changes=changes)
