"""Tests for apidiff.stats_export."""
import json
from pathlib import Path

import pytest

from apidiff.differ import Change, ChangeType, DiffResult
from apidiff.stats import compute_stats
from apidiff.stats_export import StatsExportError, export_stats, stats_to_dict


@pytest.fixture()
def sample_stats():
    result = DiffResult(
        changes=[
            Change(change_type=ChangeType.BREAKING, path="/a", method="delete", description="removed"),
            Change(change_type=ChangeType.NON_BREAKING, path="/b", method="get", description="added"),
        ]
    )
    return compute_stats(result)


def test_stats_to_dict_keys(sample_stats):
    d = stats_to_dict(sample_stats)
    for key in ("total", "breaking", "non_breaking", "breaking_ratio", "by_type", "by_method", "by_path", "affected_paths"):
        assert key in d


def test_stats_to_dict_values(sample_stats):
    d = stats_to_dict(sample_stats)
    assert d["total"] == 2
    assert d["breaking"] == 1
    assert d["non_breaking"] == 1


def test_export_stats_json(tmp_path, sample_stats):
    dest = tmp_path / "stats.json"
    export_stats(sample_stats, dest, fmt="json")
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert data["total"] == 2


def test_export_stats_text(tmp_path, sample_stats):
    dest = tmp_path / "stats.txt"
    export_stats(sample_stats, dest, fmt="text")
    assert dest.exists()
    content = dest.read_text()
    assert "Total changes" in content


def test_export_stats_unsupported_format(tmp_path, sample_stats):
    with pytest.raises(StatsExportError, match="Unsupported"):
        export_stats(sample_stats, tmp_path / "out.xml", fmt="xml")


def test_export_stats_bad_path(sample_stats):
    with pytest.raises(StatsExportError):
        export_stats(sample_stats, "/nonexistent_dir/stats.json", fmt="json")
