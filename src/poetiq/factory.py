import enum
from pathlib import Path
from typing import Type

from poetiq.action.add import AddAction
from poetiq.action.base import BaseAction
from poetiq.action.install import InstallAction
from poetiq.action.lock import LockAction
from poetiq.enums import ActionType
from poetiq.setup.db.factory import DBSetupFactory
from poetiq.setup.gitignore import GitignoreSetup
from poetiq.setup.logger import LoggerSetup
from poetiq.setup.progress_bar import ProgressBarSetup
from poetiq.setup.vscode import VSCodeSetup
from poetiq.settings.base import BaseActionSettings, BaseSetupSettings
from poetiq.settings.template import BaseTemplateSettings
from poetiq.template.app import AppTemplate
from poetiq.template.package import PackageTemplate


class ActionSetupClass(enum.Enum):
    package = PackageTemplate
    app = AppTemplate
    vscode = VSCodeSetup
    gitignore = GitignoreSetup
    logger = LoggerSetup
    progressbar = ProgressBarSetup
    add = AddAction
    install = InstallAction
    lock = LockAction

    @classmethod
    def from_action_type(cls, action_type: ActionType) -> Type[BaseAction]:
        return cls[action_type.name].value


class ActionBuilder:
    """
    Builder for concrete actions.

    Creates action in current directory.
    """

    def build(
        self, path: Path | None, settings: BaseActionSettings, core: bool
    ) -> BaseAction:
        """
        Build item setup based on item type.
        """
        action_class = self._get_action_class(settings)
        kwargs = {}
        if isinstance(settings, BaseSetupSettings) and not isinstance(
            settings, BaseTemplateSettings
        ):
            kwargs["core"] = core
        ret = action_class(path, settings, **kwargs)
        return ret

    def _get_action_class(self, settings: BaseActionSettings) -> Type[BaseAction]:
        ret = ActionSetupClass.from_action_type(settings.type)
        return ret


class PoetiqFactory:
    """
    General factory for poetiq activities.

    Creates action in given directory.
    Marks independent item setup it as core setup.
    """

    def build(self, settings: BaseActionSettings, path: Path | None) -> BaseAction:
        """
        Build item setup based on settings.

        Create builder based on settings type.
        Build setup in provided path. Default (None): build in current path
        """
        builder_class = (
            DBSetupFactory if settings.type == ActionType.db else ActionBuilder
        )
        builder = builder_class()

        ret = builder.build(path, settings, core=True)
        return ret
