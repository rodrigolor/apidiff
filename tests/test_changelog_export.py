"""Tests for apidiff.changelog_export."""

import json
from pathlib import Path

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.changelog import build_changelog
from apidiff.changelog_export import ChangelogExportError, export_changelog


@pytest.fixture()
def entry():
    result = DiffResult(
        changes=[
            Change(
                change_type=ChangeType.ENDPOINT_REMOVED,
                path="/pets",
                method="delete",
                description="Endpoint removed",
                breaking=True,
            ),
        ]
    )
    return build_changelog(result, version="1.2.0")


def test_export_text(tmp_path, entry):
    out = tmp_path / "CHANGELOG.txt"
    export_changelog(entry, out, fmt="text")
    content = out.read_text(encoding="utf-8")
    assert "Breaking Changes" in content
    assert "/pets" in content


def test_export_markdown(tmp_path, entry):
    out = tmp_path / "CHANGELOG.md"
    export_changelog(entry, out, fmt="markdown")
    content = out.read_text(encoding="utf-8")
    assert "###" in content


def test_export_json(tmp_path, entry):
    out = tmp_path / "changelog.json"
    export_changelog(entry, out, fmt="json")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["version"] == "1.2.0"
    assert isinstance(data["breaking"], list)
    assert isinstance(data["non_breaking"], list)


def test_export_unsupported_format(tmp_path, entry):
    with pytest.raises(ChangelogExportError, match="Unsupported"):
        export_changelog(entry, tmp_path / "out.xml", fmt="xml")


def test_export_creates_file(tmp_path, entry):
    out = tmp_path / "CHANGELOG.txt"
    assert not out.exists()
    export_changelog(entry, out, fmt="text")
    assert out.exists()


def test_export_json_keys(tmp_path, entry):
    out = tmp_path / "changelog.json"
    export_changelog(entry, out, fmt="json")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"version", "title", "breaking", "non_breaking"}
