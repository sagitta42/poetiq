import enum

from pydantic_parse import PydanticArgParser

from poetiq.enums import ActionType, DBType
from poetiq.settings.setup import (
    DBSettings,
    GitignoreSetupSettings,
    LoggerSettings,
    ProgressBarSettings,
    VSCodeSetupSettings,
)
from poetiq.settings.template import AppTemplateSettings, PackageTemplateSettings


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


class SetupTypeSettings(enum.Enum):
    package = PackageTemplateSettings
    app = AppTemplateSettings
    vscode = VSCodeSetupSettings
    gitignore = GitignoreSetupSettings
    logger = LoggerSettings
    progressbar = ProgressBarSettings
    db = DBSettings

    @classmethod
    def from_action_type(cls, action_type: ActionType):
        return cls[action_type.name].value


class SetupDescr(enum.StrEnum):
    app = "synchronous 3-tier request-response app template setup"
    package = "python package setup"

    @classmethod
    def from_template_type(cls, template_type: ActionType) -> str:
        return cls[template_type.name].value


def add_template_arguments(parser: PydanticArgParser):
    """
    Add arguments for new template creation.

    Create subparser for each template type.
    Add arguments of that template type to the subparser.
    """
    subparsers = parser.add_subparsers(dest="command")

    for template_type in [ActionType.package, ActionType.app]:
        t_subparser = subparsers.add_parser(
            template_type.value, help=SetupDescr.from_template_type(template_type)
        )

        settings_class = SetupTypeSettings.from_action_type(template_type)

        choices = (
            {"db_type": DBType.with_none(DBType.sql())}
            if template_type == ActionType.app
            else {}
        )
        t_subparser.add_arguments_from_model(settings_class, choices=choices)


def add_microfunctionality_arguments(parser: PydanticArgParser):
    """
    Add arguments for adding functionality to given parser.

    Create subparser for each supported setup action type.
    Add arguments of that setup to subparser.
    """

    subparsers = parser.add_subparsers(dest="command")

    for setup_type in [
        ActionType.vscode,
        ActionType.gitignore,
        ActionType.logger,
        ActionType.progressbar,
        ActionType.db,
    ]:
        setup_subparser = subparsers.add_parser(
            setup_type.value, help=f"{setup_type} setup"
        )
        settings_class = SetupTypeSettings.from_action_type(setup_type)
        choices = {"db_type": DBType.sql()} if setup_type == ActionType.db else {}
        setup_subparser.add_arguments_from_model(settings_class, choices=choices)
