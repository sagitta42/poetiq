from pathlib import Path
from typing import Literal, Self

from pydantic import model_validator
from pydantic_parse import ArgField

from poetiq.enums import ActionType, DBType
from poetiq.logger import logg
from poetiq.settings.base import BaseSetupSettings


class ItemSetupSettings(BaseSetupSettings):
    subfolder: Path = ArgField(
        default=Path(""), description="Subfolder of setup", flag=True, optional=True
    )


# TODO: subparser dest = type
class VSCodeSetupSettings(BaseSetupSettings):
    type: Literal[ActionType.vscode] = ArgField(
        default=ActionType.vscode, description="Setup type", cli=False
    )


class GitignoreSetupSettings(BaseSetupSettings):
    type: Literal[ActionType.gitignore] = ArgField(
        default=ActionType.gitignore, description="Setup type", cli=False
    )


class ProgressBarSettings(ItemSetupSettings):
    type: Literal[ActionType.progressbar] = ArgField(
        default=ActionType.progressbar, description="Setup type", cli=False
    )


class LoggerSettings(ItemSetupSettings):
    type: Literal[ActionType.logger] = ArgField(
        default=ActionType.logger, description="Setup type", cli=False
    )


class DBSettings(BaseSetupSettings):
    """
    Settings for DB setup.
    """

    type: Literal[ActionType.db] = ArgField(
        default=ActionType.db, description="Setup type", cli=False
    )
    db_type: DBType = ArgField(
        description="Database type",
        flag=True,
        optional=False,
        informative=False,
    )
    pydantic_table: bool = ArgField(
        default=False,
        flag=True,
        description="Set up pydantic-table for alembic migrations",
    )
    dev_sqlite: bool = ArgField(
        default=False, flag=True, description="Development mode switch to SQLite"
    )

    @model_validator(mode="after")
    def check_dev(self) -> Self:
        """
        Check DB type VS development mode.
        """
        # TODO: improve - separate subclasses with settings for each DB type, discriminator db_type
        if self.db_type == DBType.mongo and (self.pydantic_table or self.dev_sqlite):
            raise ValueError(
                "pydantic-table or dev-sqlite settings are not applicable for MongoDB!"
            )

        if self.dev_sqlite and self.db_type == DBType.sqlite:
            logg.warning(
                f"Development mode with switch to SQLite requested but main DB type requested is SQLite; ignoring"
            )
            self.dev_sqlite = False

        return self


class DotenvSettings(ItemSetupSettings):
    """
    Settings for .env Settings class setup
    """

    type: Literal[ActionType.envsettings] = ArgField(
        default=ActionType.envsettings, description="Setup type", cli=False
    )
