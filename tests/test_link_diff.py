"""Tests for apidiff.link_diff."""
import pytest
from apidiff.link_diff import LinkChange, LinkDiffResult, diff_links


@pytest.fixture
def base_spec():
    return {
        "paths": {
            "/orders/{id}": {
                "get": {
                    "responses": {
                        "200": {
                            "links": {
                                "GetOrderItems": {"operationRef": "#/paths/~1order-items/get"},
                                "GetUser": {"operationRef": "#/paths/~1users~1{id}/get"},
                            }
                        }
                    }
                }
            }
        }
    }


def test_no_changes_when_identical(base_spec):
    result = diff_links(base_spec, base_spec)
    assert not result.has_changes()
    assert result.total() == 0


def test_link_removed_is_breaking(base_spec):
    head = {
        "paths": {
            "/orders/{id}": {
                "get": {
                    "responses": {
                        "200": {
                            "links": {
                                "GetUser": {"operationRef": "#/paths/~1users~1{id}/get"}
                            }
                        }
                    }
                }
            }
        }
    }
    result = diff_links(base_spec, head)
    assert result.has_changes()
    assert result.has_breaking()
    removed = [c for c in result.changes if c.change_kind == "removed"]
    assert len(removed) == 1
    assert removed[0].link_name == "GetOrderItems"


def test_link_added_is_non_breaking(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/orders/{id}"]["get"]["responses"]["200"]["links"]["GetInvoice"] = {
        "operationRef": "#/paths/~1invoices~1{id}/get"
    }
    result = diff_links(base_spec, head)
    assert result.has_changes()
    assert not result.has_breaking()
    added = [c for c in result.changes if c.change_kind == "added"]
    assert any(c.link_name == "GetInvoice" for c in added)


def test_link_modified_detected(base_spec):
    import copy
    head = copy.deepcopy(base_spec)
    head["paths"]["/orders/{id}"]["get"]["responses"]["200"]["links"]["GetUser"]["operationRef"] = (
        "#/paths/~1accounts~1{id}/get"
    )
    result = diff_links(base_spec, head)
    modified = [c for c in result.changes if c.change_kind == "modified"]
    assert len(modified) == 1
    assert modified[0].link_name == "GetUser"
    assert modified[0].old_value == "#/paths/~1users~1{id}/get"
    assert modified[0].new_value == "#/paths/~1accounts~1{id}/get"


def test_link_change_str_removed():
    c = LinkChange("/orders/{id}", "get", "200", "GetOrderItems", "removed")
    assert "removed" in str(c)
    assert "GetOrderItems" in str(c)


def test_link_change_str_added():
    c = LinkChange("/orders/{id}", "get", "200", "GetInvoice", "added")
    assert "added" in str(c)


def test_link_change_str_modified():
    c = LinkChange("/orders/{id}", "get", "200", "GetUser", "modified", "old_ref", "new_ref")
    assert "old_ref" in str(c)
    assert "new_ref" in str(c)


def test_empty_spec_returns_no_changes():
    result = diff_links({}, {})
    assert not result.has_changes()


def test_diff_result_total_counts_all(base_spec):
    head = {"paths": {}}
    result = diff_links(base_spec, head)
    assert result.total() == 2
