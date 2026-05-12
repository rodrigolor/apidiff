"""Export :class:`DiffStats` to various formats."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from apidiff.stats import DiffStats, format_stats_text


class StatsExportError(Exception):
    """Raised when stats cannot be exported."""


def stats_to_dict(stats: DiffStats) -> dict:
    """Convert *stats* to a plain dictionary suitable for JSON serialisation."""
    return {
        "total": stats.total,
        "breaking": stats.breaking,
        "non_breaking": stats.non_breaking,
        "breaking_ratio": round(stats.breaking_ratio, 4),
        "by_type": stats.by_type,
        "by_method": stats.by_method,
        "by_path": stats.by_path,
        "affected_paths": stats.affected_paths,
    }


def export_stats(
    stats: DiffStats,
    dest: Union[str, Path],
    fmt: str = "json",
) -> None:
    """Write *stats* to *dest* in the requested *fmt* (``json`` or ``text``)."""
    dest = Path(dest)
    fmt = fmt.lower()

    if fmt == "json":
        payload = json.dumps(stats_to_dict(stats), indent=2)
    elif fmt == "text":
        payload = format_stats_text(stats)
    else:
        raise StatsExportError(f"Unsupported stats export format: {fmt!r}")

    try:
        dest.write_text(payload, encoding="utf-8")
    except OSError as exc:
        raise StatsExportError(f"Could not write stats to {dest}: {exc}") from exc
