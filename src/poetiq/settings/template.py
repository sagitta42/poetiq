from typing import Literal, Self, TypeVar

from pydantic import Field, model_validator
from pydantic_parse import ArgField

from poetiq.enums import ActionType, DBType
from poetiq.settings.base import BaseSetupSettings
from poetiq.settings.setup import DBSettings


class BaseTemplateSettings(BaseSetupSettings):
    """
    Common settings for any template.
    """

    type: ActionType = ArgField(
        default=ActionType.package, description="Template type", cli=False
    )
    name: str = ArgField(description="Template/repository name")

    def core_settings(self) -> dict:
        ret = self.model_dump(exclude={"no_commit": True, "update": True, "name": True}, by_alias=True)
        return ret


class PackageTemplateSettings(BaseTemplateSettings):
    """
    Package template settings.

    Include option to set up .env pydantic settings.
    """

    type: Literal[ActionType.package] = ArgField(
        default=ActionType.package, description="Template type", cli=False
    )
    settings: bool = ArgField(
        default=False, description="Set up .env Settings class", flag=True
    )
    progressbar: bool = ArgField(
        default=False, description="Set up progress bar source code", flag=True
    )
    my_base_model: bool = ArgField(
        default=False,
        description="Set up MyBaseModel class with tree display() + logger",
        flag=True,
    )


class AppTemplateSettings(BaseTemplateSettings, DBSettings):
    """
    Web app template settings.

    Web app template includes option to set up DB.

    NOTE: SQL-type DB arrives via --db-type flag while mongodb with separate bool.
    """

    type: Literal[ActionType.app] = ArgField(
        default=ActionType.app, description="Template type", cli=False
    )
    db_type: DBType = ArgField(
        default=DBType.none,
        description="Database type",
        flag=True,
        optional=True,
        informative=False,
        alias="db",
    )
    mongodb: bool = ArgField(
        default=False, description="Add MongoDB service", flag=True
    )

    @model_validator(mode="after")
    def check_db_type(self) -> Self:
        if self.db_type == DBType.mongo:
            raise ValueError(
                "Not accepting MongoDB as DB type in app settings - reserved for the mongodb setting"
            )
        return self


T_TemplateSettings = TypeVar("T_TemplateSettings", bound=BaseTemplateSettings)
