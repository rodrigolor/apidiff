"""Tests for apidiff.ignore_file module."""

import json
import textwrap

import pytest

from apidiff.differ import ChangeType
from apidiff.ignore_file import IgnoreFileError, load_ignore_config


@pytest.fixture
def json_ignore_file(tmp_path):
    data = {
        "rules": [
            {"path_prefix": "/admin"},
            {"method": "DELETE"},
            {"change_type": "endpoint_removed"},
        ]
    }
    f = tmp_path / "ignore.json"
    f.write_text(json.dumps(data))
    return str(f)


@pytest.fixture
def yaml_ignore_file(tmp_path):
    content = textwrap.dedent("""\
        rules:
          - path_prefix: /internal
          - method: PATCH
    """)
    f = tmp_path / "ignore.yaml"
    f.write_text(content)
    return str(f)


def test_load_json_ignore_file(json_ignore_file):
    config = load_ignore_config(json_ignore_file)
    assert len(config.rules) == 3


def test_json_rule_path_prefix(json_ignore_file):
    config = load_ignore_config(json_ignore_file)
    assert config.rules[0].path_prefix == "/admin"


def test_json_rule_method(json_ignore_file):
    config = load_ignore_config(json_ignore_file)
    assert config.rules[1].method == "DELETE"


def test_json_rule_change_type(json_ignore_file):
    config = load_ignore_config(json_ignore_file)
    assert config.rules[2].change_type == ChangeType.ENDPOINT_REMOVED


def test_load_yaml_ignore_file(yaml_ignore_file):
    pytest.importorskip("yaml")
    config = load_ignore_config(yaml_ignore_file)
    assert len(config.rules) == 2
    assert config.rules[0].path_prefix == "/internal"


def test_missing_file_raises(tmp_path):
    with pytest.raises(IgnoreFileError, match="not found"):
        load_ignore_config(str(tmp_path / "nonexistent.json"))


def test_unsupported_extension_raises(tmp_path):
    f = tmp_path / "ignore.toml"
    f.write_text("[rules]")
    with pytest.raises(IgnoreFileError, match="Unsupported"):
        load_ignore_config(str(f))


def test_missing_rules_key_raises(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"ignore": []}))
    with pytest.raises(IgnoreFileError, match="'rules'"):
        load_ignore_config(str(f))


def test_unknown_change_type_raises(tmp_path):
    data = {"rules": [{"change_type": "not_a_real_type"}]}
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(data))
    with pytest.raises(IgnoreFileError, match="Unknown change_type"):
        load_ignore_config(str(f))


def test_empty_rules_list(tmp_path):
    """An ignore file with an empty rules list should load without error."""
    f = tmp_path / "empty.json"
    f.write_text(json.dumps({"rules": []}))
    config = load_ignore_config(str(f))
    assert config.rules == []


def test_rule_with_multiple_fields(tmp_path):
    """A rule may combine multiple filter fields (e.g. method + path_prefix)."""
    data = {"rules": [{"method": "POST", "path_prefix": "/v1"}]}
    f = tmp_path / "multi.json"
    f.write_text(json.dumps(data))
    config = load_ignore_config(str(f))
    assert config.rules[0].method == "POST"
    assert config.rules[0].path_prefix == "/v1"
