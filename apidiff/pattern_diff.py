"""Diff pattern (regex) constraints on schema fields between two OpenAPI specs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from apidiff.differ import DiffResult


@dataclass
class PatternChange:
    path: str
    method: str
    location: str  # e.g. "param:name" or "requestBody" or "response:200"
    field_path: str  # JSON-pointer-style within schema
    old_pattern: str | None
    new_pattern: str | None

    def __str__(self) -> str:
        parts = [f"{self.method.upper()} {self.path}", f"field={self.field_path}"]
        if self.location:
            parts.append(f"location={self.location}")
        old = self.old_pattern or "<none>"
        new = self.new_pattern or "<none>"
        parts.append(f"pattern: {old!r} -> {new!r}")
        return " | ".join(parts)

    def is_breaking(self) -> bool:
        """A pattern removal or restriction change is breaking for consumers."""
        if self.old_pattern is None:
            return False  # adding a pattern is non-breaking
        if self.new_pattern is None:
            return True   # removing a pattern is breaking (was enforced)
        return self.new_pattern != self.old_pattern  # change is breaking


@dataclass
class PatternDiffResult:
    changes: list[PatternChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.changes)

    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    def total(self) -> int:
        return len(self.changes)

    def breaking(self) -> list[PatternChange]:
        return [c for c in self.changes if c.is_breaking()]

    def non_breaking(self) -> list[PatternChange]:
        return [c for c in self.changes if not c.is_breaking()]


def _iter_schema_patterns(schema: dict, prefix: str = "") -> Iterator[tuple[str, str | None]]:
    """Yield (field_path, pattern) pairs from a schema recursively."""
    if not isinstance(schema, dict):
        return
    if "pattern" in schema:
        yield prefix, schema["pattern"]
    for prop_name, prop_schema in schema.get("properties", {}).items():
        yield from _iter_schema_patterns(prop_schema, f"{prefix}/properties/{prop_name}")
    for i, item_schema in enumerate(schema.get("items", []) if isinstance(schema.get("items"), list) else ([schema["items"]] if "items" in schema else [])):
        yield from _iter_schema_patterns(item_schema, f"{prefix}/items")


def _collect_patterns(schema: dict, prefix: str = "") -> dict[str, str]:
    return dict(_iter_schema_patterns(schema, prefix))


def diff_patterns(base_spec: dict, head_spec: dict) -> PatternDiffResult:
    """Compare pattern constraints across all operations in two specs."""
    result = PatternDiffResult()
    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})
    all_paths = set(base_paths) | set(head_paths)

    for path in all_paths:
        base_ops = base_paths.get(path, {})
        head_ops = head_paths.get(path, {})
        all_methods = set(base_ops) | set(head_ops)

        for method in all_methods:
            if method not in ("get", "post", "put", "patch", "delete", "options", "head"):
                continue
            base_op = base_ops.get(method, {})
            head_op = head_ops.get(method, {})

            # Parameters
            base_params = {p["name"]: p for p in base_op.get("parameters", []) if isinstance(p, dict) and "name" in p}
            head_params = {p["name"]: p for p in head_op.get("parameters", []) if isinstance(p, dict) and "name" in p}
            for pname in set(base_params) | set(head_params):
                bp = _collect_patterns(base_params.get(pname, {}).get("schema", {}))
                hp = _collect_patterns(head_params.get(pname, {}).get("schema", {}))
                for fp in set(bp) | set(hp):
                    if bp.get(fp) != hp.get(fp):
                        result.changes.append(PatternChange(
                            path=path, method=method,
                            location=f"param:{pname}", field_path=fp or "/",
                            old_pattern=bp.get(fp), new_pattern=hp.get(fp),
                        ))

            # Request body
            base_body_schema = base_op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
            head_body_schema = head_op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
            bp = _collect_patterns(base_body_schema)
            hp = _collect_patterns(head_body_schema)
            for fp in set(bp) | set(hp):
                if bp.get(fp) != hp.get(fp):
                    result.changes.append(PatternChange(
                        path=path, method=method,
                        location="requestBody", field_path=fp or "/",
                        old_pattern=bp.get(fp), new_pattern=hp.get(fp),
                    ))

            # Responses
            base_responses = base_op.get("responses", {})
            head_responses = head_op.get("responses", {})
            for status in set(base_responses) | set(head_responses):
                base_resp_schema = base_responses.get(status, {}).get("content", {}).get("application/json", {}).get("schema", {})
                head_resp_schema = head_responses.get(status, {}).get("content", {}).get("application/json", {}).get("schema", {})
                bp = _collect_patterns(base_resp_schema)
                hp = _collect_patterns(head_resp_schema)
                for fp in set(bp) | set(hp):
                    if bp.get(fp) != hp.get(fp):
                        result.changes.append(PatternChange(
                            path=path, method=method,
                            location=f"response:{status}", field_path=fp or "/",
                            old_pattern=bp.get(fp), new_pattern=hp.get(fp),
                        ))

    return result
