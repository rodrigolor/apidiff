"""Unit tests for TagCoverageResult dataclass properties."""
from apidiff.tag_coverage import TagCoverageResult


def test_coverage_ratio_zero_operations():
    r = TagCoverageResult(total_operations=0, tagged_operations=0)
    assert r.coverage_ratio == 1.0


def test_coverage_ratio_partial():
    r = TagCoverageResult(total_operations=4, tagged_operations=1)
    assert r.coverage_ratio == 0.25


def test_coverage_percent_rounds_two_decimals():
    r = TagCoverageResult(total_operations=3, tagged_operations=1)
    # 1/3 = 33.333... -> 33.33
    assert r.coverage_percent == 33.33


def test_is_fully_tagged_true():
    r = TagCoverageResult(total_operations=5, tagged_operations=5)
    assert r.is_fully_tagged is True


def test_is_fully_tagged_false_when_partial():
    r = TagCoverageResult(total_operations=5, tagged_operations=4)
    assert r.is_fully_tagged is False


def test_is_fully_tagged_false_when_no_operations():
    r = TagCoverageResult(total_operations=0, tagged_operations=0)
    assert r.is_fully_tagged is False


def test_default_untagged_paths_empty():
    r = TagCoverageResult()
    assert r.untagged_paths == []


def test_default_tag_counts_empty():
    r = TagCoverageResult()
    assert r.tag_counts == {}
