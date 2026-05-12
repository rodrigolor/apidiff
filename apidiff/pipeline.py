"""Pipeline for chaining diff filters, sorting, and ignore rules."""

from typing import List, Optional

from apidiff.differ import ChangeType, DiffResult
from apidiff.filter import (
    filter_breaking,
    filter_by_method,
    filter_by_path,
    filter_non_breaking,
)
from apidiff.ignorer import IgnoreConfig, IgnoreRule, apply_ignore
from apidiff.sorter import sort_changes


class DiffPipeline:
    """Fluent builder for applying transformations to a DiffResult."""

    def __init__(self, result: DiffResult) -> None:
        self._result = result

    def breaking_only(self) -> "DiffPipeline":
        self._result = filter_breaking(self._result)
        return self

    def non_breaking_only(self) -> "DiffPipeline":
        self._result = filter_non_breaking(self._result)
        return self

    def path(self, prefix: str) -> "DiffPipeline":
        self._result = filter_by_path(self._result, prefix)
        return self

    def method(self, http_method: str) -> "DiffPipeline":
        self._result = filter_by_method(self._result, http_method)
        return self

    def sort(self, by: str = "severity", ascending: bool = True) -> "DiffPipeline":
        self._result = sort_changes(self._result, by=by, ascending=ascending)
        return self

    def ignore(self, config: IgnoreConfig) -> "DiffPipeline":
        """Apply an IgnoreConfig to suppress matching changes."""
        self._result = apply_ignore(self._result, config)
        return self

    def ignore_paths(self, prefixes: List[str]) -> "DiffPipeline":
        """Ignore all changes whose path starts with any of the given prefixes."""
        config = IgnoreConfig(rules=[IgnoreRule(path_prefix=p) for p in prefixes])
        return self.ignore(config)

    def ignore_change_types(self, types: List[ChangeType]) -> "DiffPipeline":
        """Ignore changes of the given ChangeType values."""
        config = IgnoreConfig(rules=[IgnoreRule(change_type=t) for t in types])
        return self.ignore(config)

    def build(self) -> DiffResult:
        return self._result
