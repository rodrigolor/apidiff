"""CLI entry point for apidiff."""

import sys

import click

from apidiff import __version__
from apidiff.loader import SpecLoadError, load_spec


@click.command()
@click.argument("base", metavar="BASE_SPEC")
@click.argument("revision", metavar="REVISION_SPEC")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format for the diff report.",
)
@click.version_option(version=__version__, prog_name="apidiff")
def main(base: str, revision: str, output_format: str) -> None:
    """Diff two OpenAPI spec files and highlight breaking vs non-breaking changes.

    BASE_SPEC    Path to the base (original) OpenAPI spec file.
    REVISION_SPEC  Path to the revised OpenAPI spec file.
    """
    try:
        base_spec = load_spec(base)
        revision_spec = load_spec(revision)
    except SpecLoadError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(
        f"Loaded base spec: {base_spec.get('info', {}).get('title', 'unknown')} "
        f"v{base_spec.get('info', {}).get('version', '?')}"
    )
    click.echo(
        f"Loaded revision spec: {revision_spec.get('info', {}).get('title', 'unknown')} "
        f"v{revision_spec.get('info', {}).get('version', '?')}"
    )
    click.echo(f"Output format: {output_format}")
    click.echo("(diff engine not yet implemented)")


if __name__ == "__main__":
    main()
