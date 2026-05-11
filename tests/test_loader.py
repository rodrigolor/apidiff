"""Tests for the spec loader module."""

import json
import textwrap

import pytest

from apidiff.loader import SpecLoadError, load_spec


MINIMAL_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {},
}


@pytest.fixture()
def json_spec_file(tmp_path):
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(MINIMAL_SPEC), encoding="utf-8")
    return spec_file


@pytest.fixture()
def yaml_spec_file(tmp_path):
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(
        textwrap.dedent("""\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0.0"
            paths: {}
        """),
        encoding="utf-8",
    )
    return spec_file


def test_load_json_spec(json_spec_file):
    spec = load_spec(str(json_spec_file))
    assert spec["openapi"] == "3.0.0"
    assert spec["info"]["title"] == "Test API"


def test_load_yaml_spec(yaml_spec_file):
    spec = load_spec(str(yaml_spec_file))
    assert spec["openapi"] == "3.0.0"
    assert spec["info"]["version"] == "1.0.0"


def test_load_yml_extension(tmp_path):
    spec_file = tmp_path / "spec.yml"
    spec_file.write_text(json.dumps(MINIMAL_SPEC), encoding="utf-8")
    spec = load_spec(str(spec_file))
    assert spec["paths"] == {}


def test_file_not_found():
    with pytest.raises(SpecLoadError, match="File not found"):
        load_spec("/nonexistent/path/spec.json")


def test_unsupported_extension(tmp_path):
    spec_file = tmp_path / "spec.txt"
    spec_file.write_text("{}", encoding="utf-8")
    with pytest.raises(SpecLoadError, match="Unsupported file format"):
        load_spec(str(spec_file))


def test_invalid_json(tmp_path):
    spec_file = tmp_path / "bad.json"
    spec_file.write_text("{ not valid json ", encoding="utf-8")
    with pytest.raises(SpecLoadError, match="Failed to parse"):
        load_spec(str(spec_file))


def test_invalid_yaml(tmp_path):
    spec_file = tmp_path / "bad.yaml"
    spec_file.write_text("key: [unclosed", encoding="utf-8")
    with pytest.raises(SpecLoadError, match="Failed to parse"):
        load_spec(str(spec_file))


def test_path_is_directory(tmp_path):
    with pytest.raises(SpecLoadError, match="Path is not a file"):
        load_spec(str(tmp_path))
