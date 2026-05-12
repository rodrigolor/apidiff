"""Tests for apidiff.changelog."""

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.changelog import (
    ChangelogEntry,
    build_changelog,
    format_changelog_text,
)


@pytest.fixture()
def empty_result():
    return DiffResult(changes=[])


@pytest.fixture()
def mixed_result():
    return DiffResult(
        changes=[
            Change(
                change_type=ChangeType.ENDPOINT_REMOVED,
                path="/users",
                method="get",
                description="Endpoint removed",
                breaking=True,
            ),
            Change(
                change_type=ChangeType.ENDPOINT_ADDED,
                path="/orders",
                method="post",
                description="Endpoint added",
                breaking=False,
            ),
        ]
    )


def test_build_changelog_empty(empty_result):
    entry = build_changelog(empty_result, version="1.1.0")
    assert entry.version == "1.1.0"
    assert entry.breaking == []
    assert entry.non_breaking == []


def test_build_changelog_breaking_count(mixed_result):
    entry = build_changelog(mixed_result, version="2.0.0")
    assert len(entry.breaking) == 1
    assert len(entry.non_breaking) == 1


def test_build_changelog_custom_title(mixed_result):
    entry = build_changelog(mixed_result, version="2.0.0", title="My Release")
    assert entry.title == "My Release"


def test_build_changelog_default_title(empty_result):
    entry = build_changelog(empty_result, version="3.0.0")
    assert "3.0.0" in entry.title


def test_format_text_no_changes(empty_result):
    entry = build_changelog(empty_result, version="1.0.0")
    text = format_changelog_text(entry)
    assert "No changes detected" in text


def test_format_text_breaking_section(mixed_result):
    entry = build_changelog(mixed_result, version="2.0.0")
    text = format_changelog_text(entry)
    assert "Breaking Changes" in text
    assert "Non-Breaking Changes" in text


def test_format_text_contains_path(mixed_result):
    entry = build_changelog(mixed_result, version="2.0.0")
    text = format_changelog_text(entry)
    assert "/users" in text
    assert "/orders" in text


def test_format_text_method_uppercase(mixed_result):
    entry = build_changelog(mixed_result, version="2.0.0")
    text = format_changelog_text(entry)
    assert "GET" in text
    assert "POST" in text
