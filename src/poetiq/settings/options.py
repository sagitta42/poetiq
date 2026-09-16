from typing import Annotated, Union

from pydantic import BaseModel, Field

from poetiq.settings.poetiq_action import AddSettings, InstallSettings, LockSettings
from poetiq.settings.setup import (
    DBSettings,
    GitignoreSetupSettings,
    LoggerSettings,
    ProgressBarSettings,
    VSCodeSetupSettings,
)
from poetiq.settings.template import AppTemplateSettings, PackageTemplateSettings

AcceptedActionSettings = Annotated[
    PackageTemplateSettings
    | AppTemplateSettings
    | VSCodeSetupSettings
    | GitignoreSetupSettings
    | LoggerSettings
    | ProgressBarSettings
    | DBSettings
    | InstallSettings
    | AddSettings
    | LockSettings,
    Field(discriminator="type"),
]


class ActionOptions(BaseModel):
    """
    Exists for convenience of constructing and validating accepted action settings.
    """

    settings: AcceptedActionSettings


AcceptedTemplateSettings = Annotated[
    PackageTemplateSettings | AppTemplateSettings,
    Field(discriminator="type"),
]


class TemplateOptions(BaseModel):
    """
    Exists for convenience of constructing and validating accepted template options.
    """

    settings: AcceptedTemplateSettings


SettingsOptions = Union[ActionOptions, TemplateOptions]
