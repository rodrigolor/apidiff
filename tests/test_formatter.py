"""Tests for the formatter module."""

import io
import json

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.formatter import format_json, format_text


@pytest.fixture
def empty_result():
    return DiffResult()


@pytest.fixture
def mixed_result():
    return DiffResult(changes=[
        Change(ChangeType.BREAKING, "/users", "endpoint removed"),
        Change(ChangeType.NON_BREAKING, "/orders", "endpoint added"),
        Change(ChangeType.INFO, "info.version", "version changed from '1.0' to '2.0'",
               old_value="1.0", new_value="2.0"),
    ])


def test_format_text_no_changes(empty_result):
    out = io.StringIO()
    format_text(empty_result, out=out, use_color=False)
    assert "No changes detected" in out.getvalue()


def test_format_text_breaking_label(mixed_result):
    out = io.StringIO()
    format_text(mixed_result, out=out, use_color=False)
    text = out.getvalue()
    assert "Breaking changes" in text
    assert "/users" in text


def test_format_text_non_breaking_label(mixed_result):
    out = io.StringIO()
    format_text(mixed_result, out=out, use_color=False)
    text = out.getvalue()
    assert "Non-breaking changes" in text
    assert "/orders" in text


def test_format_text_info_label(mixed_result):
    out = io.StringIO()
    format_text(mixed_result, out=out, use_color=False)
    text = out.getvalue()
    assert "Info" in text
    assert "info.version" in text


def test_format_text_summary_line(mixed_result):
    out = io.StringIO()
    format_text(mixed_result, out=out, use_color=False)
    text = out.getvalue()
    assert "Summary:" in text
    assert "1 breaking" in text
    assert "1 non-breaking" in text
    assert "1 info" in text


def test_format_json_structure(mixed_result):
    data = format_json(mixed_result)
    assert data["has_breaking_changes"] is True
    assert data["summary"]["breaking"] == 1
    assert data["summary"]["non_breaking"] == 1
    assert data["summary"]["info"] == 1
    assert len(data["changes"]) == 3


def test_format_json_change_fields(mixed_result):
    data = format_json(mixed_result)
    version_change = next(c for c in data["changes"] if c["type"] == "info")
    assert version_change["old_value"] == "1.0"
    assert version_change["new_value"] == "2.0"
    assert "version changed" in version_change["message"]


def test_format_json_no_changes(empty_result):
    data = format_json(empty_result)
    assert data["has_breaking_changes"] is False
    assert data["changes"] == []
    assert data["summary"]["breaking"] == 0


def test_format_json_serialisable(mixed_result):
    data = format_json(mixed_result)
    # Should not raise
    serialised = json.dumps(data)
    parsed = json.loads(serialised)
    assert parsed["summary"]["breaking"] == 1
