from pydantic import Field, model_validator
from typing import Literal, Optional, Self

from pydantic_parse import ArgField

from poetiq.enums import ActionType
from poetiq.exceptions import PoetiqException
from poetiq.settings.base import BaseSplitActionSettings


class InstallSettings(BaseSplitActionSettings):
    """
    poetiq install settings
    """

    type: Literal[ActionType.install] = ArgField(
        default=ActionType.install, description="Action type", cli=False
    )
    split: Optional[str] = ArgField(
        default=None,
        description="Install from split pyproject.toml files (all defined in poetiq.toml or given DIR)",
        flag=True,
        optional=True,
        informative=True,
        const="",
    )
    local: bool = ArgField(
        default=False,
        description="Install local dependencies defined in poetiq.toml",
        flag=True,
    )
    package: str = ArgField(
        default="",
        description="Specific package to install in split or local model; otherwise all local/split",
        optional=True
    )


class AddSettings(BaseSplitActionSettings):
    """
    poetiq add settings

    Note that unlike the install or lock actions,
        add action does not allow to perform add
        to ALL split directories, and requires specific one to be provided.
    """

    type: Literal[ActionType.add] = ArgField(
        default=ActionType.add, description="Action type", cli=False
    )
    package: str = ArgField(description="Package source (name, https, git)")
    split: Optional[str] = ArgField(
        default=None,
        description="Add to split pyproject.toml file in specified DIR",
        flag=True,
        optional=True,
    )
    local: str = ArgField(
        default="",
        description="Add local dependency to poetiq.toml in given path",
        optional=True,
        flag=True,
    )

    @model_validator(mode="after")
    def check_split_local(self) -> Self:
        """
        Split and local are mutually exclusive options.
        """
        if self.split and self.local:
            raise PoetiqException(
                "Provide either --split or --local argument, not both!"
            )
        return self

    @model_validator(mode="after")
    def check_split_dir(self) -> Self:
        """
        Adding to all split dirs (split="") is not allowed.
        """
        if self.split == "":
            raise PoetiqException(
                "Provide specific split directory or none! (add to all split not allowed)"
            )
        return self


class LockSettings(BaseSplitActionSettings):
    type: Literal[ActionType.lock] = ArgField(
        default=ActionType.lock, description="Action type", cli=False
    )
    split: Optional[str] = ArgField(
        default=None,
        description="Update split poetry.lock(s) (all or specified DIR)",
        optional=True,
        flag=True,
        informative=True,
        const="",
    )

    @property
    def split_requested(self) -> bool:
        return self.split is not None
