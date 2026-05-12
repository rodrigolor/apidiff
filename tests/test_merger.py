"""Tests for apidiff.merger."""

import pytest

from apidiff.merger import MergeError, merge_specs


@pytest.fixture()
def base_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Base", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"summary": "List", "responses": {"200": {"description": "OK"}}}
            }
        },
    }


@pytest.fixture()
def overlay_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Overlay", "version": "2.0.0"},
        "paths": {
            "/items": {
                "get": {"summary": "Items", "responses": {"200": {"description": "OK"}}}
            }
        },
    }


def test_merge_adds_overlay_paths(base_spec, overlay_spec):
    result = merge_specs(base_spec, overlay_spec)
    assert "/users" in result["paths"]
    assert "/items" in result["paths"]


def test_overlay_title_wins(base_spec, overlay_spec):
    result = merge_specs(base_spec, overlay_spec)
    assert result["info"]["title"] == "Overlay"


def test_base_not_mutated(base_spec, overlay_spec):
    merge_specs(base_spec, overlay_spec)
    assert "/items" not in base_spec["paths"]


def test_overlay_not_mutated(base_spec, overlay_spec):
    merge_specs(base_spec, overlay_spec)
    assert "/users" not in overlay_spec["paths"]


def test_version_mismatch_raises(base_spec):
    bad_overlay = {"openapi": "3.1.0", "paths": {}}
    with pytest.raises(MergeError, match="version mismatch"):
        merge_specs(base_spec, bad_overlay)


def test_version_mismatch_allowed(base_spec):
    bad_overlay = {"openapi": "3.1.0", "paths": {}}
    result = merge_specs(base_spec, bad_overlay, allow_version_mismatch=True)
    assert result["openapi"] == "3.1.0"


def test_deep_merge_operation_level():
    base = {
        "openapi": "3.0.0",
        "paths": {"/a": {"get": {"summary": "old", "deprecated": False}}},
    }
    overlay = {
        "openapi": "3.0.0",
        "paths": {"/a": {"get": {"summary": "new"}}},
    }
    result = merge_specs(base, overlay)
    assert result["paths"]["/a"]["get"]["summary"] == "new"
    assert result["paths"]["/a"]["get"]["deprecated"] is False
