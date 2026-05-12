"""Tests for apidiff.tagger module."""
import pytest
from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.tagger import (
    TaggedChange,
    TagReport,
    tag_change,
    build_tag_report,
    format_tag_report_text,
    _extract_tags,
)


@pytest.fixture
def base_spec():
    return {
        "paths": {
            "/users": {
                "get": {"tags": ["users"], "summary": "List users"},
                "post": {"tags": ["users", "admin"], "summary": "Create user"},
            },
            "/items": {
                "delete": {"summary": "Delete item"},  # no tags
            },
        }
    }


@pytest.fixture
def head_spec():
    return {
        "paths": {
            "/users": {
                "get": {"tags": ["users"], "summary": "List users"},
            }
        }
    }


@pytest.fixture
def mixed_result():
    return DiffResult(
        changes=[
            Change(change_type=ChangeType.ENDPOINT_REMOVED, path="/users", method="post", breaking=True),
            Change(change_type=ChangeType.ENDPOINT_ADDED, path="/users", method="get", breaking=False),
            Change(change_type=ChangeType.ENDPOINT_REMOVED, path="/items", method="delete", breaking=True),
        ]
    )


def test_extract_tags_found(base_spec):
    tags = _extract_tags("/users", "get", base_spec)
    assert tags == ["users"]


def test_extract_tags_multiple(base_spec):
    tags = _extract_tags("/users", "post", base_spec)
    assert "users" in tags
    assert "admin" in tags


def test_extract_tags_missing_path(base_spec):
    tags = _extract_tags("/nonexistent", "get", base_spec)
    assert tags == []


def test_extract_tags_no_path_arg(base_spec):
    tags = _extract_tags(None, "get", base_spec)
    assert tags == []


def test_tag_change_uses_head_spec(base_spec, head_spec):
    change = Change(change_type=ChangeType.ENDPOINT_ADDED, path="/users", method="get", breaking=False)
    tc = tag_change(change, base_spec, head_spec)
    assert "users" in tc.tags


def test_tag_change_falls_back_to_base(base_spec, head_spec):
    change = Change(change_type=ChangeType.ENDPOINT_REMOVED, path="/users", method="post", breaking=True)
    tc = tag_change(change, base_spec, head_spec)
    assert "users" in tc.tags
    assert "admin" in tc.tags


def test_tag_change_primary_tag(base_spec, head_spec):
    change = Change(change_type=ChangeType.ENDPOINT_ADDED, path="/users", method="get", breaking=False)
    tc = tag_change(change, base_spec, head_spec)
    assert tc.primary_tag == "users"


def test_tag_change_untagged(base_spec, head_spec):
    change = Change(change_type=ChangeType.ENDPOINT_REMOVED, path="/items", method="delete", breaking=True)
    tc = tag_change(change, base_spec, head_spec)
    assert tc.tags == []
    assert tc.primary_tag is None


def test_build_tag_report_groups_by_tag(mixed_result, base_spec, head_spec):
    report = build_tag_report(mixed_result, base_spec, head_spec)
    assert "users" in report.by_tag
    assert len(report.by_tag["users"]) >= 1


def test_build_tag_report_untagged(mixed_result, base_spec, head_spec):
    report = build_tag_report(mixed_result, base_spec, head_spec)
    assert len(report.untagged) == 1
    assert report.untagged[0].change.path == "/items"


def test_build_tag_report_total(mixed_result, base_spec, head_spec):
    report = build_tag_report(mixed_result, base_spec, head_spec)
    assert report.total == 3


def test_format_tag_report_text_contains_tag(mixed_result, base_spec, head_spec):
    report = build_tag_report(mixed_result, base_spec, head_spec)
    text = format_tag_report_text(report)
    assert "[users]" in text


def test_format_tag_report_text_contains_untagged(mixed_result, base_spec, head_spec):
    report = build_tag_report(mixed_result, base_spec, head_spec)
    text = format_tag_report_text(report)
    assert "[untagged]" in text


def test_format_tag_report_text_empty():
    report = TagReport()
    text = format_tag_report_text(report)
    assert text == "No changes to tag."
