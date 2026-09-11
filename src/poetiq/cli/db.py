import argparse
from typing import Type

from poetiq.cli.args import add_bool, add_str
from poetiq.settings.base import BaseSetupSettings


def add_db_arguments(
    parser: argparse.ArgumentParser,
    help: Type[BaseSetupSettings],
    choices: list[str],
    optional: bool,
):
    """
    Add arguments for DB setup to given parser.

    help: pydantic model to use for description; default, and const values.
        (can be DBSettings or AppTemplateSettings, for example)
    """
    add_str(
        parser,
        "db-type",
        help=help,
        optional=optional,
        informative=False,
        choices=choices,
    )

    add_bool(parser, "dev-sqlite", help=help)
    add_bool(parser, "pydantic-table", help=help)
