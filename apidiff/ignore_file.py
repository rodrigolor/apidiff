"""Load ignore rules from a YAML or JSON ignore-config file."""

import json
from pathlib import Path
from typing import Any, Dict, List

from apidiff.differ import ChangeType
from apidiff.ignorer import IgnoreConfig, IgnoreRule


class IgnoreFileError(Exception):
    """Raised when an ignore file cannot be parsed."""


_CHANGE_TYPE_MAP: Dict[str, ChangeType] = {
    ct.value: ct for ct in ChangeType
}


def _parse_rule(raw: Dict[str, Any]) -> IgnoreRule:
    """Parse a single rule dict into an IgnoreRule."""
    change_type = None
    if "change_type" in raw:
        key = raw["change_type"]
        if key not in _CHANGE_TYPE_MAP:
            raise IgnoreFileError(f"Unknown change_type: '{key}'")
        change_type = _CHANGE_TYPE_MAP[key]
    return IgnoreRule(
        path_prefix=raw.get("path_prefix"),
        method=raw.get("method"),
        change_type=change_type,
    )


def load_ignore_config(path: str) -> IgnoreConfig:
    """Load an IgnoreConfig from a JSON or YAML file."""
    p = Path(path)
    if not p.exists():
        raise IgnoreFileError(f"Ignore file not found: {path}")

    suffix = p.suffix.lower()
    try:
        raw_text = p.read_text(encoding="utf-8")
        if suffix == ".json":
            data = json.loads(raw_text)
        elif suffix in (".yaml", ".yml"):
            try:
                import yaml
            except ImportError as exc:
                raise IgnoreFileError("PyYAML is required to load YAML ignore files") from exc
            data = yaml.safe_load(raw_text)
        else:
            raise IgnoreFileError(f"Unsupported ignore file format: {suffix}")
    except (json.JSONDecodeError, Exception) as exc:
        raise IgnoreFileError(f"Failed to parse ignore file: {exc}") from exc

    if not isinstance(data, dict) or "rules" not in data:
        raise IgnoreFileError("Ignore file must contain a top-level 'rules' list")

    config = IgnoreConfig()
    for raw_rule in data["rules"]:
        config.add_rule(_parse_rule(raw_rule))
    return config
