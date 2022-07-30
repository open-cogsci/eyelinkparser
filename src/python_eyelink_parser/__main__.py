"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Python Eyelink Parser."""


if __name__ == "__main__":
    main(prog_name="python-eyelinkparser")  # pragma: no cover
