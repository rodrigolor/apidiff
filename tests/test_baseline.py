"""Tests for apidiff.baseline."""

import json
import pytest

from apidiff.baseline import (
    BaselineError,
    load_baseline,
    save_baseline,
    subtract_baseline,
)
from apidiff.differ import Change, ChangeType, DiffResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_result():
    return DiffResult(
        changes=[
            Change(ChangeType.BREAKING, "/pets", "get", "endpoint removed"),
            Change(ChangeType.NON_BREAKING, "/pets", "post", "response description changed"),
        ]
    )


@pytest.fixture()
def empty_result():
    return DiffResult(changes=[])


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path, sample_result):
    dest = tmp_path / "baseline.json"
    save_baseline(sample_result, dest)
    assert dest.exists()


def test_save_load_roundtrip(tmp_path, sample_result):
    dest = tmp_path / "baseline.json"
    save_baseline(sample_result, dest)
    loaded = load_baseline(dest)
    assert len(loaded.changes) == len(sample_result.changes)
    for orig, restored in zip(sample_result.changes, loaded.changes):
        assert restored.change_type == orig.change_type
        assert restored.path == orig.path
        assert restored.method == orig.method
        assert restored.description == orig.description


def test_save_empty_result(tmp_path, empty_result):
    dest = tmp_path / "baseline.json"
    save_baseline(empty_result, dest)
    loaded = load_baseline(dest)
    assert loaded.changes == []


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(BaselineError, match="Cannot read baseline"):
        load_baseline(tmp_path / "nonexistent.json")


def test_load_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(BaselineError, match="Invalid baseline file"):
        load_baseline(bad)


def test_load_missing_key_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"wrong_key": []}), encoding="utf-8")
    with pytest.raises(BaselineError, match="Invalid baseline file"):
        load_baseline(bad)


# ---------------------------------------------------------------------------
# subtract_baseline
# ---------------------------------------------------------------------------

def test_subtract_removes_known_changes(sample_result):
    baseline = DiffResult(changes=[sample_result.changes[0]])
    result = subtract_baseline(sample_result, baseline)
    assert len(result.changes) == 1
    assert result.changes[0].description == "response description changed"


def test_subtract_empty_baseline_returns_all(sample_result, empty_result):
    result = subtract_baseline(sample_result, empty_result)
    assert len(result.changes) == len(sample_result.changes)


def test_subtract_identical_baseline_returns_empty(sample_result):
    result = subtract_baseline(sample_result, sample_result)
    assert result.changes == []
