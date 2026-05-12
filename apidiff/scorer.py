"""Severity scoring for API diff results."""
from dataclasses import dataclass
from typing import Dict

from apidiff.differ import ChangeType, DiffResult

# Base scores per change type
_SCORES: Dict[ChangeType, int] = {
    ChangeType.ENDPOINT_REMOVED: 100,
    ChangeType.OPERATION_REMOVED: 90,
    ChangeType.PARAMETER_REMOVED: 70,
    ChangeType.PARAMETER_TYPE_CHANGED: 60,
    ChangeType.RESPONSE_REMOVED: 80,
    ChangeType.RESPONSE_TYPE_CHANGED: 50,
    ChangeType.ENDPOINT_ADDED: 5,
    ChangeType.OPERATION_ADDED: 5,
    ChangeType.PARAMETER_ADDED: 10,
    ChangeType.RESPONSE_ADDED: 5,
}

_DEFAULT_BREAKING_SCORE = 50
_DEFAULT_NON_BREAKING_SCORE = 5


@dataclass
class ScoreResult:
    total: int
    breaking_score: int
    non_breaking_score: int
    change_count: int
    breaking_count: int

    @property
    def risk_level(self) -> str:
        if self.total == 0:
            return "none"
        if self.total < 50:
            return "low"
        if self.total < 150:
            return "medium"
        return "high"


def score_change(change_type: ChangeType) -> int:
    """Return the numeric severity score for a single change type."""
    return _SCORES.get(change_type, _DEFAULT_BREAKING_SCORE if _is_breaking(change_type) else _DEFAULT_NON_BREAKING_SCORE)


def _is_breaking(change_type: ChangeType) -> bool:
    from apidiff.differ import breaking as _breaking_set
    return change_type in _breaking_set


def score_result(result: DiffResult) -> ScoreResult:
    """Compute an aggregate severity score for a DiffResult."""
    total = 0
    breaking_score = 0
    non_breaking_score = 0
    breaking_count = 0

    for change in result.changes:
        s = score_change(change.change_type)
        total += s
        if _is_breaking(change.change_type):
            breaking_score += s
            breaking_count += 1
        else:
            non_breaking_score += s

    return ScoreResult(
        total=total,
        breaking_score=breaking_score,
        non_breaking_score=non_breaking_score,
        change_count=len(result.changes),
        breaking_count=breaking_count,
    )
