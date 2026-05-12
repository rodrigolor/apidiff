"""Module for ignoring specific changes during diff comparison."""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from apidiff.differ import Change, ChangeType, DiffResult


@dataclass
class IgnoreRule:
    """A rule that specifies which changes to ignore."""
    path_prefix: Optional[str] = None
    method: Optional[str] = None
    change_type: Optional[ChangeType] = None

    def matches(self, change: Change) -> bool:
        """Return True if this rule matches the given change."""
        if self.path_prefix and not change.path.startswith(self.path_prefix):
            return False
        if self.method and change.method and change.method.upper() != self.method.upper():
            return False
        if self.change_type and change.change_type != self.change_type:
            return False
        return True


@dataclass
class IgnoreConfig:
    """Collection of ignore rules."""
    rules: List[IgnoreRule] = field(default_factory=list)

    def add_rule(self, rule: IgnoreRule) -> None:
        self.rules.append(rule)

    def should_ignore(self, change: Change) -> bool:
        """Return True if any rule matches the given change."""
        return any(rule.matches(change) for rule in self.rules)


def apply_ignore(result: DiffResult, config: IgnoreConfig) -> DiffResult:
    """Filter out changes that match any ignore rule."""
    filtered = [c for c in result.changes if not config.should_ignore(c)]
    return DiffResult(changes=filtered)


def ignore_paths(result: DiffResult, prefixes: List[str]) -> DiffResult:
    """Convenience: ignore all changes under given path prefixes."""
    config = IgnoreConfig(rules=[IgnoreRule(path_prefix=p) for p in prefixes])
    return apply_ignore(result, config)


def ignore_change_types(result: DiffResult, types: List[ChangeType]) -> DiffResult:
    """Convenience: ignore changes of specific ChangeType values."""
    config = IgnoreConfig(rules=[IgnoreRule(change_type=t) for t in types])
    return apply_ignore(result, config)
