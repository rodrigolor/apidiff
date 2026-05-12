"""Generate status badge data from a ScoreResult."""
from dataclasses import dataclass
from typing import Literal

from apidiff.scorer import ScoreResult

Color = Literal["brightgreen", "green", "yellow", "orange", "red"]

_RISK_COLORS: dict = {
    "none": "brightgreen",
    "low": "green",
    "medium": "yellow",
    "high": "red",
}


@dataclass
class BadgeData:
    label: str
    message: str
    color: Color
    schema_url: str = "https://shields.io/endpoint"

    def to_dict(self) -> dict:
        return {
            "schemaVersion": 1,
            "label": self.label,
            "message": self.message,
            "color": self.color,
        }


def make_badge(score: ScoreResult, label: str = "api-diff") -> BadgeData:
    """Build badge data from a ScoreResult."""
    risk = score.risk_level
    color: Color = _RISK_COLORS.get(risk, "red")

    if risk == "none":
        message = "no changes"
    elif score.breaking_count == 0:
        message = f"{score.change_count} non-breaking"
    else:
        message = f"{score.breaking_count} breaking"

    return BadgeData(label=label, message=message, color=color)
