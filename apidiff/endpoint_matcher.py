"""Fuzzy endpoint matcher: finds renamed or similar endpoints between two specs."""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

from apidiff.differ import DiffResult


@dataclass
class EndpointMatch:
    """Represents a potential rename/move between two endpoint paths."""

    old_path: str
    new_path: str
    score: float  # 0.0 – 1.0 similarity score

    def __str__(self) -> str:
        return f"{self.old_path} -> {self.new_path} (score={self.score:.2f})"


@dataclass
class MatchReport:
    """Collection of endpoint matches produced by the matcher."""

    matches: List[EndpointMatch] = field(default_factory=list)
    unmatched_old: List[str] = field(default_factory=list)
    unmatched_new: List[str] = field(default_factory=list)

    @property
    def total_matches(self) -> int:
        return len(self.matches)

    @property
    def has_matches(self) -> bool:
        return bool(self.matches)


def _similarity(a: str, b: str) -> float:
    """Return a similarity ratio between two path strings."""
    return SequenceMatcher(None, a, b).ratio()


def _best_match(path: str, candidates: List[str], threshold: float) -> Optional[Tuple[str, float]]:
    """Return the best matching candidate above *threshold*, or None."""
    best: Optional[Tuple[str, float]] = None
    for candidate in candidates:
        score = _similarity(path, candidate)
        if score >= threshold and (best is None or score > best[1]):
            best = (candidate, score)
    return best


def find_endpoint_matches(
    old_paths: List[str],
    new_paths: List[str],
    threshold: float = 0.6,
) -> MatchReport:
    """Match removed endpoints to added endpoints using fuzzy path similarity.

    Args:
        old_paths: Paths present in the base spec.
        new_paths: Paths present in the head spec.
        threshold: Minimum similarity score (0–1) to consider a match.

    Returns:
        A :class:`MatchReport` with matched pairs and unmatched leftovers.
    """
    remaining_new = list(new_paths)
    matches: List[EndpointMatch] = []
    unmatched_old: List[str] = []

    for old in old_paths:
        result = _best_match(old, remaining_new, threshold)
        if result is not None:
            matched_new, score = result
            matches.append(EndpointMatch(old_path=old, new_path=matched_new, score=score))
            remaining_new.remove(matched_new)
        else:
            unmatched_old.append(old)

    return MatchReport(
        matches=matches,
        unmatched_old=unmatched_old,
        unmatched_new=remaining_new,
    )


def match_from_diff(diff: DiffResult, threshold: float = 0.6) -> MatchReport:
    """Convenience wrapper that extracts removed/added paths from a DiffResult."""
    from apidiff.differ import ChangeType  # local import to avoid cycles

    old_paths = [
        c.path for c in diff.changes if c.change_type == ChangeType.ENDPOINT_REMOVED
    ]
    new_paths = [
        c.path for c in diff.changes if c.change_type == ChangeType.ENDPOINT_ADDED
    ]
    return find_endpoint_matches(old_paths, new_paths, threshold=threshold)
