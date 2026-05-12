"""Tests for apidiff.patcher."""

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.patcher import PatchError, apply_patch


@pytest.fixture()
def base_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"summary": "List users", "responses": {"200": {"description": "OK"}}}
            }
        },
    }


@pytest.fixture()
def empty_diff():
    return DiffResult(changes=[])


@pytest.fixture()
def added_endpoint_diff():
    return DiffResult(
        changes=[
            Change(
                change_type=ChangeType.ADDED,
                path="/items",
                method=None,
                description="Endpoint /items added",
            )
        ]
    )


@pytest.fixture()
def added_method_diff():
    return DiffResult(
        changes=[
            Change(
                change_type=ChangeType.ADDED,
                path="/users",
                method="POST",
                description="POST /users added",
            )
        ]
    )


def test_apply_empty_diff_returns_copy(base_spec, empty_diff):
    result = apply_patch(base_spec, empty_diff)
    assert result == base_spec
    assert result is not base_spec


def test_apply_added_endpoint(base_spec, added_endpoint_diff):
    result = apply_patch(base_spec, added_endpoint_diff)
    assert "/items" in result["paths"]


def test_apply_added_method(base_spec, added_method_diff):
    result = apply_patch(base_spec, added_method_diff)
    assert "post" in result["paths"]["/users"]


def test_removed_changes_are_not_applied(base_spec):
    diff = DiffResult(
        changes=[
            Change(
                change_type=ChangeType.REMOVED,
                path="/users",
                method="GET",
                description="GET /users removed",
            )
        ]
    )
    result = apply_patch(base_spec, diff)
    assert "get" in result["paths"]["/users"]


def test_does_not_mutate_original(base_spec, added_endpoint_diff):
    original_paths = set(base_spec["paths"].keys())
    apply_patch(base_spec, added_endpoint_diff)
    assert set(base_spec["paths"].keys()) == original_paths


def test_patch_error_on_missing_paths():
    spec = {"openapi": "3.0.0"}
    diff = DiffResult(
        changes=[
            Change(
                change_type=ChangeType.ADDED,
                path="/new",
                method=None,
                description="added",
            )
        ]
    )
    with pytest.raises(PatchError):
        apply_patch(spec, diff)
