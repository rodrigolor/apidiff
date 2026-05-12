"""Command-line interface for apidiff."""
import sys
import argparse
import json

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ import diff_specs
from apidiff.formatter import format_text, format_json
from apidiff.reporter import summarize, format_summary_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apidiff",
        description="Diff two OpenAPI spec files and highlight breaking vs non-breaking changes.",
    )
    parser.add_argument("base", help="Path to the base (old) OpenAPI spec file.")
    parser.add_argument("head", help="Path to the head (new) OpenAPI spec file.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary of changes after the diff output.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        base_spec = load_spec(args.base)
        head_spec = load_spec(args.head)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 1

    result = diff_specs(base_spec, head_spec)

    if args.format == "json":
        print(format_json(result))
    else:
        print(format_text(result, color=not args.no_color))

    if args.summary:
        summary = summarize(result)
        print()
        print(format_summary_text(summary))

    return 1 if result.has_breaking else 0


if __name__ == "__main__":
    sys.exit(main())
