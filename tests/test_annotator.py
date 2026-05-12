"""Tests for apidiff.annotator."""

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.annotator import (
    AnnotatedChange,
    annotate_change,
    annotate_result,
    format_annotated_text,
)


@pytest.fixture
def breaking_change():
    return Change(
        change_type=ChangeType.BREAKING,
        path="/users",
        method="get",
        field="endpoint_removed",
        detail="Path /users was removed",
    )


@pytest.fixture
def non_breaking_change():
    return Change(
        change_type=ChangeType.NON_BREAKING,
        path="/items",
        method="post",
        field="endpoint_added",
        detail="Path /items was added",
    )


@pytest.fixture
def mixed_result(breaking_change, non_breaking_change):
    return DiffResult(changes=[breaking_change, non_breaking_change])


@pytest.fixture
def empty_result():
    return DiffResult(changes=[])


def test_annotate_change_title_known_field(breaking_change):
    ann = annotate_change(breaking_change)
    assert ann.title == "Endpoint Removed"


def test_annotate_change_title_unknown_field():
    change = Change(
        change_type=ChangeType.NON_BREAKING,
        path="/foo",
        method=None,
        field="some_custom_field",
        detail="something",
    )
    ann = annotate_change(change)
    assert ann.title == "Some Custom Field"


def test_annotate_change_is_breaking(breaking_change):
    ann = annotate_change(breaking_change)
    assert ann.is_breaking() is True


def test_annotate_change_is_not_breaking(non_breaking_change):
    ann = annotate_change(non_breaking_change)
    assert ann.is_breaking() is False


def test_annotate_change_migration_hint_present(breaking_change):
    ann = annotate_change(breaking_change)
    assert ann.migration_hint is not None
    assert "client" in ann.migration_hint.lower()


def test_annotate_change_no_hint_for_added(non_breaking_change):
    ann = annotate_change(non_breaking_change)
    assert ann.migration_hint is None


def test_annotate_change_tags_include_severity(breaking_change):
    ann = annotate_change(breaking_change)
    assert ChangeType.BREAKING.value in ann.tags


def test_annotate_change_tags_include_method(breaking_change):
    ann = annotate_change(breaking_change)
    assert "GET" in ann.tags


def test_annotate_result_length(mixed_result):
    annotated = annotate_result(mixed_result)
    assert len(annotated) == 2


def test_annotate_result_empty(empty_result):
    annotated = annotate_result(empty_result)
    assert annotated == []


def test_format_annotated_text_empty():
    text = format_annotated_text([])
    assert "No changes" in text


def test_format_annotated_text_breaking_label(mixed_result):
    annotated = annotate_result(mixed_result)
    text = format_annotated_text(annotated)
    assert "[BREAKING]" in text


def test_format_annotated_text_non_breaking_label(mixed_result):
    annotated = annotate_result(mixed_result)
    text = format_annotated_text(annotated)
    assert "[non-breaking]" in text


def test_format_annotated_text_includes_hint(mixed_result):
    annotated = annotate_result(mixed_result)
    text = format_annotated_text(annotated)
    assert "Hint:" in text
