"""Diff examples/request-body between two OpenAPI specs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ExampleChange:
    path: str
    method: str
    location: str  # e.g. "requestBody", "responses/200"
    field: str     # e.g. "example", "examples/foo"
    change_type: str  # "added", "removed", "modified"
    base_value: Any
    head_value: Any

    def __str__(self) -> str:
        parts = [self.method.upper(), self.path, self.location, self.field]
        return f"[{self.change_type}] {' > '.join(parts)}"

    def is_breaking(self) -> bool:
        """Example removals are considered non-breaking by convention."""
        return False


@dataclass
class ExampleDiffResult:
    changes: list[ExampleChange]

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def total(self) -> int:
        return len(self.changes)


def _extract_examples(operation: dict[str, Any]) -> dict[str, Any]:
    """Return a flat dict of example keys -> values from an operation."""
    examples: dict[str, Any] = {}

    # requestBody examples
    req_body = operation.get("requestBody", {})
    for media_type, media_obj in req_body.get("content", {}).items():
        if "example" in media_obj:
            examples[f"requestBody/{media_type}/example"] = media_obj["example"]
        for name, ex in media_obj.get("examples", {}).items():
            examples[f"requestBody/{media_type}/examples/{name}"] = ex

    # response examples
    for status, resp_obj in operation.get("responses", {}).items():
        for media_type, media_obj in resp_obj.get("content", {}).items():
            if "example" in media_obj:
                examples[f"responses/{status}/{media_type}/example"] = media_obj["example"]
            for name, ex in media_obj.get("examples", {}).items():
                examples[f"responses/{status}/{media_type}/examples/{name}"] = ex

    return examples


def diff_examples(base_spec: dict, head_spec: dict) -> ExampleDiffResult:
    """Compare examples across all paths/methods between base and head specs."""
    changes: list[ExampleChange] = []
    http_methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}

    base_paths = base_spec.get("paths", {})
    head_paths = head_spec.get("paths", {})
    all_paths = set(base_paths) | set(head_paths)

    for path in sorted(all_paths):
        base_path_item = base_paths.get(path, {})
        head_path_item = head_paths.get(path, {})
        all_methods = (set(base_path_item) | set(head_path_item)) & http_methods

        for method in sorted(all_methods):
            base_op = base_path_item.get(method, {})
            head_op = head_path_item.get(method, {})
            base_examples = _extract_examples(base_op)
            head_examples = _extract_examples(head_op)
            all_keys = set(base_examples) | set(head_examples)

            for key in sorted(all_keys):
                location, _, field = key.rpartition("/")
                if key not in base_examples:
                    changes.append(ExampleChange(path, method, location, field, "added", None, head_examples[key]))
                elif key not in head_examples:
                    changes.append(ExampleChange(path, method, location, field, "removed", base_examples[key], None))
                elif base_examples[key] != head_examples[key]:
                    changes.append(ExampleChange(path, method, location, field, "modified", base_examples[key], head_examples[key]))

    return ExampleDiffResult(changes=changes)
