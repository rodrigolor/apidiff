"""Baseline management: save and load a DiffResult as a baseline for future comparisons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from apidiff.differ import Change, ChangeType, DiffResult


class BaselineError(Exception):
    """Raised when a baseline file cannot be read or written."""


def _change_to_dict(change: Change) -> dict:
    return {
        "change_type": change.change_type.value,
        "path": change.path,
        "method": change.method,
        "description": change.description,
    }


def _change_from_dict(data: dict) -> Change:
    return Change(
        change_type=ChangeType(data["change_type"]),
        path=data["path"],
        method=data.get("method"),
        description=data["description"],
    )


def save_baseline(result: DiffResult, filepath: Union[str, Path]) -> None:
    """Persist *result* to *filepath* as JSON so it can be used as a baseline."""
    filepath = Path(filepath)
    payload = {"changes": [_change_to_dict(c) for c in result.changes]}
    try:
        filepath.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise BaselineError(f"Cannot write baseline to '{filepath}': {exc}") from exc


def load_baseline(filepath: Union[str, Path]) -> DiffResult:
    """Load a previously saved baseline from *filepath* and return a DiffResult."""
    filepath = Path(filepath)
    try:
        raw = filepath.read_text(encoding="utf-8")
    except OSError as exc:
        raise BaselineError(f"Cannot read baseline from '{filepath}': {exc}") from exc

    try:
        payload = json.loads(raw)
        changes = [_change_from_dict(c) for c in payload["changes"]]
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        raise BaselineError(f"Invalid baseline file '{filepath}': {exc}") from exc

    return DiffResult(changes=changes)


def subtract_baseline(current: DiffResult, baseline: DiffResult) -> DiffResult:
    """Return only the changes in *current* that are **not** present in *baseline*.

    Two changes are considered identical when their (change_type, path, method,
    description) tuple matches.
    """
    baseline_keys = {
        (c.change_type, c.path, c.method, c.description) for c in baseline.changes
    }
    new_changes = [
        c
        for c in current.changes
        if (c.change_type, c.path, c.method, c.description) not in baseline_keys
    ]
    return DiffResult(changes=new_changes)
