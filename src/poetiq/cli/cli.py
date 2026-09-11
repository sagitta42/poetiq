import argparse
import enum

from poetiq.cli.args import add_bool, add_str
from poetiq.cli.db import add_db_arguments
from poetiq.enums import ActionType, DBType
from poetiq.settings.base import BaseSetupSettings
from poetiq.settings.setup import DBSettings, LoggerSettings
from poetiq.settings.template import (
    AppTemplateSettings,
    BaseTemplateSettings,
    PackageTemplateSettings,
)


class Subparser(enum.StrEnum):
    new = "new"
    update = "update"
    setup = "setup"
    init = "init"
    install = "install"
    add = "add"
    lock = "lock"

    def descr(self) -> str:
        ret = f"poetry {self} with advanced options"
        return ret


def add_template_arguments(parser: argparse.ArgumentParser):
    """
    Add arguments for new template creation.
    """
    add_str(parser, "name", help=BaseTemplateSettings, optional=False, flag=False)

    add_str(
        parser,
        "type",
        help=BaseTemplateSettings,
        optional=True,
        informative=False,
        choices=[
            setup_type.value for setup_type in [ActionType.package, ActionType.app]
        ],
    )

    add_db_arguments(
        parser,
        AppTemplateSettings,
        optional=True,
        choices=DBType.with_none(DBType.sql()),
    )

    add_bool(parser, "mongodb", AppTemplateSettings, exclusive=True)

    add_bool(parser, "settings", PackageTemplateSettings, exclusive=True, optional=True)
    add_bool(
        parser, "progressbar", PackageTemplateSettings, exclusive=True, optional=True
    )
    add_bool(
        parser, "my-base-model", PackageTemplateSettings, optional=True, exclusive=True
    )


def add_microfunctionality_arguments(parser: argparse.ArgumentParser):
    """
    Add arguments for adding functionality to given parser.

    Create subparser for each supported setup action type.
    Add arguments of that setup to subparser.
    """

    subparsers = parser.add_subparsers(dest="command")

    for setup_type in [ActionType.vscode, ActionType.gitignore, ActionType.logger]:
        setup_subparser = subparsers.add_parser(
            setup_type.value, help=f"{setup_type} setup"
        )
        add_bool(setup_subparser, "no-commit", BaseSetupSettings)

        if setup_type == ActionType.logger:
            add_str(
                setup_subparser,
                "subfolder",
                LoggerSettings,
                optional=True,
                informative=False,
            )

    db_subparser = subparsers.add_parser(
        ActionType.db.value, help=f"{ActionType.db} setup"
    )
    # TODO: db type in DB subparser as non-flag
    add_db_arguments(db_subparser, DBSettings, optional=False, choices=DBType.sql())
