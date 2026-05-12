"""Tests for apidiff.exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.exporter import ExportError, export_result, SUPPORTED_FORMATS


@pytest.fixture()
def mixed_result() -> DiffResult:
    return DiffResult(
        changes=[
            Change(
                change_type=ChangeType.ENDPOINT_REMOVED,
                path="/users",
                method="GET",
                description="Endpoint removed",
                breaking=True,
            ),
            Change(
                change_type=ChangeType.ENDPOINT_ADDED,
                path="/items",
                method="POST",
                description="Endpoint added",
                breaking=False,
            ),
        ]
    )


@pytest.fixture()
def empty_result() -> DiffResult:
    return DiffResult(changes=[])


def test_export_json(tmp_path: Path, mixed_result: DiffResult) -> None:
    out = tmp_path / "report.json"
    returned = export_result(mixed_result, out, fmt="json")
    assert returned == out.resolve()
    data = json.loads(out.read_text())
    assert "changes" in data
    assert len(data["changes"]) == 2


def test_export_text(tmp_path: Path, mixed_result: DiffResult) -> None:
    out = tmp_path / "report.txt"
    export_result(mixed_result, out, fmt="text")
    content = out.read_text()
    assert "BREAKING" in content or "NON-BREAKING" in content


def test_export_markdown(tmp_path: Path, mixed_result: DiffResult) -> None:
    out = tmp_path / "report.md"
    export_result(mixed_result, out, fmt="markdown")
    content = out.read_text()
    assert "# API Diff Report" in content
    assert "Breaking Changes" in content
    assert "Non-Breaking Changes" in content


def test_export_markdown_empty(tmp_path: Path, empty_result: DiffResult) -> None:
    out = tmp_path / "empty.md"
    export_result(empty_result, out, fmt="markdown")
    content = out.read_text()
    assert "No changes detected" in content


def test_export_creates_parent_dirs(tmp_path: Path, mixed_result: DiffResult) -> None:
    out = tmp_path / "nested" / "deep" / "report.json"
    export_result(mixed_result, out, fmt="json")
    assert out.exists()


def test_export_unsupported_format(tmp_path: Path, mixed_result: DiffResult) -> None:
    with pytest.raises(ExportError, match="Unsupported format"):
        export_result(mixed_result, tmp_path / "out.xml", fmt="xml")


def test_export_case_insensitive_format(tmp_path: Path, mixed_result: DiffResult) -> None:
    out = tmp_path / "report.json"
    export_result(mixed_result, out, fmt="JSON")
    assert out.exists()


def test_supported_formats_constant() -> None:
    assert "json" in SUPPORTED_FORMATS
    assert "markdown" in SUPPORTED_FORMATS
    assert "text" in SUPPORTED_FORMATS
