"""Export score and badge data to files or stdout."""
import json
from pathlib import Path
from typing import Optional

from apidiff.differ import DiffResult
from apidiff.scorer import ScoreResult, score_result
from apidiff.badge import BadgeData, make_badge


class ScoreExportError(Exception):
    """Raised when score export fails."""


def score_summary_dict(score: ScoreResult, badge: BadgeData) -> dict:
    """Combine score and badge data into a single exportable dict."""
    return {
        "score": {
            "total": score.total,
            "breaking": score.breaking_score,
            "non_breaking": score.non_breaking_score,
            "change_count": score.change_count,
            "breaking_count": score.breaking_count,
            "risk_level": score.risk_level,
        },
        "badge": badge.to_dict(),
    }


def export_score(
    result: DiffResult,
    output_path: Optional[str] = None,
    badge_label: str = "api-diff",
) -> dict:
    """Compute score and badge, optionally writing JSON to *output_path*.

    Returns the summary dict regardless of whether a file is written.
    """
    score = score_result(result)
    badge = make_badge(score, label=badge_label)
    data = score_summary_dict(score, badge)

    if output_path is not None:
        try:
            Path(output_path).write_text(json.dumps(data, indent=2))
        except OSError as exc:
            raise ScoreExportError(f"Failed to write score file: {exc}") from exc

    return data


def format_score_text(score: ScoreResult) -> str:
    """Return a human-readable summary of the score."""
    lines = [
        f"Risk level  : {score.risk_level.upper()}",
        f"Total score : {score.total}",
        f"  Breaking  : {score.breaking_score} ({score.breaking_count} changes)",
        f"  Non-break : {score.non_breaking_score} ({score.change_count - score.breaking_count} changes)",
    ]
    return "\n".join(lines)
