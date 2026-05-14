"""Tests for apidiff.server_diff."""

import pytest

from apidiff.differ import ChangeType
from apidiff.server_diff import ServerChange, ServerDiffResult, diff_servers


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0"},
        "servers": [
            {"url": "https://api.example.com", "description": "Production"},
            {"url": "https://staging.example.com", "description": "Staging"},
        ],
        "paths": {},
    }


def test_no_changes_when_identical(base_spec):
    result = diff_servers(base_spec, base_spec)
    assert not result.has_changes()
    assert result.total() == 0
    assert not result.has_breaking()


def test_server_removed_is_breaking(base_spec):
    head = dict(base_spec)
    head["servers"] = [{"url": "https://api.example.com", "description": "Production"}]
    result = diff_servers(base_spec, head)
    assert result.has_changes()
    assert result.has_breaking()
    removed = [c for c in result.changes if c.change_type == ChangeType.REMOVED]
    assert len(removed) == 1
    assert removed[0].url == "https://staging.example.com"


def test_server_added_is_non_breaking(base_spec):
    head = dict(base_spec)
    head["servers"] = base_spec["servers"] + [{"url": "https://new.example.com"}]
    result = diff_servers(base_spec, head)
    assert result.has_changes()
    assert not result.has_breaking()
    added = [c for c in result.changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].url == "https://new.example.com"


def test_description_change_is_non_breaking(base_spec):
    head = dict(base_spec)
    head["servers"] = [
        {"url": "https://api.example.com", "description": "Prod (updated)"},
        {"url": "https://staging.example.com", "description": "Staging"},
    ]
    result = diff_servers(base_spec, head)
    assert result.has_changes()
    assert not result.has_breaking()
    modified = [c for c in result.changes if c.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].field == "description"


def test_no_servers_key_treated_as_empty():
    base = {"openapi": "3.0.0", "info": {"title": "A", "version": "1"}, "paths": {}}
    head = {"openapi": "3.0.0", "info": {"title": "A", "version": "1"}, "paths": {},
            "servers": [{"url": "https://api.example.com"}]}
    result = diff_servers(base, head)
    assert result.has_changes()
    assert not result.has_breaking()


def test_server_change_str_removed():
    c = ServerChange(url="https://api.example.com", change_type=ChangeType.REMOVED)
    assert "removed" in str(c).lower()
    assert "https://api.example.com" in str(c)


def test_server_change_str_added():
    c = ServerChange(url="https://new.example.com", change_type=ChangeType.ADDED)
    assert "added" in str(c).lower()


def test_server_change_str_modified():
    c = ServerChange(
        url="https://api.example.com",
        change_type=ChangeType.MODIFIED,
        old_value="Production",
        new_value="Prod",
        field="description",
    )
    assert "description" in str(c)
    assert "Production" in str(c)


def test_summary_text_no_changes(base_spec):
    result = diff_servers(base_spec, base_spec)
    assert "No server changes" in result.summary_text()


def test_summary_text_with_changes(base_spec):
    head = dict(base_spec)
    head["servers"] = [{"url": "https://api.example.com", "description": "Production"}]
    result = diff_servers(base_spec, head)
    text = result.summary_text()
    assert "BREAKING" in text
    assert "staging.example.com" in text
