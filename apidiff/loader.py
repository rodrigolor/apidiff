"""Loader module for reading and parsing OpenAPI spec files."""

import json
import pathlib
from typing import Any

import yaml


class SpecLoadError(Exception):
    """Raised when a spec file cannot be loaded or parsed."""


def load_spec(path: str) -> dict[str, Any]:
    """Load an OpenAPI spec from a JSON or YAML file.

    Args:
        path: Path to the OpenAPI spec file (.json, .yaml, or .yml).

    Returns:
        Parsed spec as a dictionary.

    Raises:
        SpecLoadError: If the file cannot be read or parsed.
    """
    file_path = pathlib.Path(path)

    if not file_path.exists():
        raise SpecLoadError(f"File not found: {path}")

    if not file_path.is_file():
        raise SpecLoadError(f"Path is not a file: {path}")

    suffix = file_path.suffix.lower()
    if suffix not in (".json", ".yaml", ".yml"):
        raise SpecLoadError(
            f"Unsupported file format '{suffix}'. Expected .json, .yaml, or .yml."
        )

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecLoadError(f"Cannot read file {path}: {exc}") from exc

    try:
        if suffix == ".json":
            spec = json.loads(content)
        else:
            spec = yaml.safe_load(content) or {}
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise SpecLoadError(f"Failed to parse {path}: {exc}") from exc

    if not isinstance(spec, dict):
        raise SpecLoadError(
            f"Invalid spec in {path}: expected a mapping at the top level, "
            f"got {type(spec).__name__}."
        )

    return spec
