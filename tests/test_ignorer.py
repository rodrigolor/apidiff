"""Tests for apidiff.ignorer module."""

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.ignorer import (
    IgnoreConfig,
    IgnoreRule,
    apply_ignore,
    ignore_change_types,
    ignore_paths,
)


@pytest.fixture
def mixed_result():
    return DiffResult(
        changes=[
            Change(change_type=ChangeType.ENDPOINT_REMOVED, path="/users", method="GET", description="Endpoint removed"),
            Change(change_type=ChangeType.ENDPOINT_ADDED, path="/users", method="POST", description="Endpoint added"),
            Change(change_type=ChangeType.ENDPOINT_REMOVED, path="/admin/settings", method="DELETE", description="Admin endpoint removed"),
            Change(change_type=ChangeType.RESPONSE_CHANGED, path="/items", method="GET", description="Response changed"),
        ]
    )


def test_ignore_rule_matches_path_prefix(mixed_result):
    rule = IgnoreRule(path_prefix="/admin")
    matches = [c for c in mixed_result.changes if rule.matches(c)]
    assert len(matches) == 1
    assert matches[0].path == "/admin/settings"


def test_ignore_rule_matches_method(mixed_result):
    rule = IgnoreRule(method="GET")
    matches = [c for c in mixed_result.changes if rule.matches(c)]
    assert len(matches) == 2


def test_ignore_rule_matches_change_type(mixed_result):
    rule = IgnoreRule(change_type=ChangeType.ENDPOINT_REMOVED)
    matches = [c for c in mixed_result.changes if rule.matches(c)]
    assert len(matches) == 2


def test_ignore_rule_combined(mixed_result):
    rule = IgnoreRule(path_prefix="/users", method="GET")
    matches = [c for c in mixed_result.changes if rule.matches(c)]
    assert len(matches) == 1
    assert matches[0].method == "GET"


def test_apply_ignore_removes_matching(mixed_result):
    config = IgnoreConfig(rules=[IgnoreRule(path_prefix="/admin")])
    result = apply_ignore(mixed_result, config)
    assert all(not c.path.startswith("/admin") for c in result.changes)
    assert len(result.changes) == 3


def test_apply_ignore_empty_rules(mixed_result):
    config = IgnoreConfig()
    result = apply_ignore(mixed_result, config)
    assert len(result.changes) == len(mixed_result.changes)


def test_ignore_paths_convenience(mixed_result):
    result = ignore_paths(mixed_result, ["/admin", "/items"])
    assert len(result.changes) == 2
    assert all(c.path == "/users" for c in result.changes)


def test_ignore_change_types_convenience(mixed_result):
    result = ignore_change_types(mixed_result, [ChangeType.ENDPOINT_REMOVED])
    assert all(c.change_type != ChangeType.ENDPOINT_REMOVED for c in result.changes)
    assert len(result.changes) == 2


def test_ignore_config_should_ignore(mixed_result):
    config = IgnoreConfig()
    config.add_rule(IgnoreRule(change_type=ChangeType.ENDPOINT_ADDED))
    ignored = [c for c in mixed_result.changes if config.should_ignore(c)]
    assert len(ignored) == 1
    assert ignored[0].change_type == ChangeType.ENDPOINT_ADDED
