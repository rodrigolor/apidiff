"""Diff numeric and string constraints (min, max, minLength, maxLength, etc.)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

CONSTRAINT_FIELDS = [
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minLength", "maxLength", "minItems", "maxItems",
    "minProperties", "maxProperties", "multipleOf",
]


@dataclass
class ConstraintChange:
    path: str
    method: str
    param_or_field: str
    constraint: str
    old_value: Any
    new_value: Any

    def __str__(self) -> str:
        return (
            f"{self.method.upper()} {self.path} "
            f"[{self.param_or_field}] {self.constraint}: "
            f"{self.old_value!r} -> {self.new_value!r}"
        )

    def is_breaking(self) -> bool:
        """Tightening a constraint is breaking; relaxing is non-breaking."""
        tightening = {
            "minimum": lambda o, n: n > o,
            "exclusiveMinimum": lambda o, n: n > o,
            "maximum": lambda o, n: n < o,
            "exclusiveMaximum": lambda o, n: n < o,
            "minLength": lambda o, n: n > o,
            "maxLength": lambda o, n: n < o,
            "minItems": lambda o, n: n > o,
            "maxItems": lambda o, n: n < o,
            "minProperties": lambda o, n: n > o,
            "maxProperties": lambda o, n: n < o,
            "multipleOf": lambda o, n: o is None and n is not None,
        }
        fn = tightening.get(self.constraint)
        if fn is None:
            return False
        try:
            return fn(self.old_value, self.new_value)
        except TypeError:
            return False


@dataclass
class ConstraintDiffResult:
    changes: List[ConstraintChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.changes)

    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    def total(self) -> int:
        return len(self.changes)


def _diff_schema_constraints(
    path: str, method: str, label: str,
    base_schema: Dict, head_schema: Dict,
    result: ConstraintDiffResult,
) -> None:
    for key in CONSTRAINT_FIELDS:
        old_val = base_schema.get(key)
        new_val = head_schema.get(key)
        if old_val != new_val:
            result.changes.append(
                ConstraintChange(
                    path=path, method=method,
                    param_or_field=label,
                    constraint=key,
                    old_value=old_val,
                    new_value=new_val,
                )
            )


def diff_constraints(
    base_spec: Dict, head_spec: Dict
) -> ConstraintDiffResult:
    result = ConstraintDiffResult()
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})

    for path, base_ops in base_paths.items():
        head_ops = head_paths.get(path, {})
        for method, base_op in base_ops.items():
            if not isinstance(base_op, dict):
                continue
            head_op = head_ops.get(method, {}) if isinstance(head_ops, dict) else {}

            # Parameters
            base_params = {p["name"]: p for p in base_op.get("parameters", []) if "name" in p}
            head_params = {p["name"]: p for p in head_op.get("parameters", []) if "name" in p}
            for pname, bp in base_params.items():
                hp = head_params.get(pname, {})
                bs = bp.get("schema", {})
                hs = hp.get("schema", {})
                _diff_schema_constraints(path, method, f"param:{pname}", bs, hs, result)

            # Request body
            base_rb = base_op.get("requestBody", {})
            head_rb = head_op.get("requestBody", {})
            for mt, base_mt_obj in base_rb.get("content", {}).items():
                head_mt_obj = head_rb.get("content", {}).get(mt, {})
                bs = base_mt_obj.get("schema", {})
                hs = head_mt_obj.get("schema", {})
                _diff_schema_constraints(path, method, f"requestBody:{mt}", bs, hs, result)

    return result
