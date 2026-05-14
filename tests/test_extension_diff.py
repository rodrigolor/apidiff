"""Tests for apidiff.extension_diff and apidiff.extension_diff_pipeline."""
import json
import os
import tempfile

import pytest

from apidiff.extension_diff import (
    ExtensionChange,
    diff_extensions,
)
from apidiff.extension_diff_pipeline import run_extension_diff_pipeline


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "x-internal": True,
        "x-owner": "team-a",
        "paths": {
            "/users": {
                "x-stability": "stable",
                "get": {
                    "x-rate-limit": 100,
                    "responses": {"200": {"description": "OK"}},
                },
            }
        },
    }


def test_no_changes_when_identical(base_spec):
    result = diff_extensions(base_spec, base_spec)
    assert not result.has_changes
    assert result.total == 0


def test_top_level_extension_removed(base_spec):
    head = {**base_spec, "x-owner": None}
    # None means absent — rebuild without key
    head = {k: v for k, v in base_spec.items() if k != "x-owner"}
    result = diff_extensions(base_spec, head)
    keys = [c.key for c in result.changes]
    assert "x-owner" in keys
    removed = next(c for c in result.changes if c.key == "x-owner")
    assert removed.old_value == "team-a"
    assert removed.new_value is None


def test_top_level_extension_added(base_spec):
    head = {**base_spec, "x-new-field": "hello"}
    result = diff_extensions(base_spec, head)
    keys = [c.key for c in result.changes]
    assert "x-new-field" in keys
    added = next(c for c in result.changes if c.key == "x-new-field")
    assert added.old_value is None
    assert added.new_value == "hello"


def test_top_level_extension_changed(base_spec):
    head = {**base_spec, "x-internal": False}
    result = diff_extensions(base_spec, head)
    changed = next(c for c in result.changes if c.key == "x-internal")
    assert changed.old_value is True
    assert changed.new_value is False


def test_operation_extension_changed(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/users"]["get"]["x-rate-limit"] = 50
    result = diff_extensions(base_spec, head)
    op_changes = [c for c in result.changes if c.path == "/users" and c.method == "get"]
    assert len(op_changes) == 1
    assert op_changes[0].key == "x-rate-limit"
    assert op_changes[0].old_value == 100
    assert op_changes[0].new_value == 50


def test_path_level_extension_changed(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/users"]["x-stability"] = "experimental"
    result = diff_extensions(base_spec, head)
    path_changes = [c for c in result.changes if c.path == "/users" and c.method is None]
    assert any(c.key == "x-stability" for c in path_changes)


def test_extension_change_str_added():
    c = ExtensionChange(key="x-foo", path=None, method=None, old_value=None, new_value="bar")
    assert "added" in str(c)
    assert "x-foo" in str(c)


def test_extension_change_str_removed():
    c = ExtensionChange(key="x-foo", path="/a", method="get", old_value="old", new_value=None)
    assert "removed" in str(c)
    assert "GET /a" in str(c)


def test_extension_change_str_changed():
    c = ExtensionChange(key="x-foo", path="/a", method=None, old_value=1, new_value=2)
    assert "->" in str(c)


def _write(tmp_path, name, data):
    p = os.path.join(tmp_path, name)
    with open(p, "w") as f:
        json.dump(data, f)
    return p


def test_pipeline_returns_result_type(tmp_path, base_spec):
    p1 = _write(tmp_path, "base.json", base_spec)
    p2 = _write(tmp_path, "head.json", base_spec)
    result = run_extension_diff_pipeline(p1, p2)
    assert not result.has_changes
    assert "No vendor extension" in result.summary_text()


def test_pipeline_detects_change(tmp_path, base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["x-owner"] = "team-b"
    p1 = _write(tmp_path, "base.json", base_spec)
    p2 = _write(tmp_path, "head.json", head)
    result = run_extension_diff_pipeline(p1, p2)
    assert result.has_changes
    assert result.total >= 1
    text = result.summary_text()
    assert "x-owner" in text
