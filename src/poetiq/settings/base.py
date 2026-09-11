from abc import abstractmethod
import enum
from typing import Any, Optional, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field
from pydantic.fields import FieldInfo
from pydantic_parse import ArgField, ArgModel

from poetiq.enums import ActionType


class BaseActionSettings(ArgModel):
    """
    Base class for settings for any action.

    Adaptor utils to argparse.
    """

    model_config = ConfigDict(extra="ignore")
    type: ActionType = ArgField(description="Action type")

    # @classmethod
    # def alias(cls, arg: str) -> str:
    #     ret = cls._get_field(arg).alias or arg
    #     return ret

    # @classmethod
    # def description(cls, arg: str, exclusive: bool = False) -> str:
    #     """
    #     Field description util for argparse.

    #     exclusive: add note that it is exclusive for this type of template.
    #     """
    #     field = cls.arg_fields()[arg]
    #     ret = field.description
    #     assert ret is not None
    #     if exclusive:
    #         template_type = field.default("type")
    #         ret += f" ({template_type} only)"
    #     return ret


class BasePoetiqActionSettings(BaseActionSettings):
    """
    Base class for poetiq action settings.
    """

    pass


class BaseSplitActionSettings(BasePoetiqActionSettings):
    """
    Common settings for a split poetiq action.

    True split poetiq action, if requested, can be performed on all split directories
        or a specific given one.

    split=None - no split requested
    split="" - all directories
    split="name" - given directory

    --split flag not provided -> default = None (no split requested)
    --split flag provided with no argument -> const = "" (all directories)
    """

    split: Optional[str] = ArgField(
        default=None,
        description="Split directory",
        const="",
        flag=True,
        optional=True,
        informative=True,
    )

    @property
    def split_requested(self) -> bool:
        return self.split is not None


class BaseSetupSettings(BaseActionSettings):
    """
    Base class for settings for any type of setup.
    """

    type: ActionType = ArgField(description="Setup type")
    no_commit: bool = ArgField(
        default=False, description="Do not commit changes", flag=True
    )


T_ActionSettings = TypeVar("T_ActionSettings", bound=BaseActionSettings)
T_PoetiqActionSettings = TypeVar(
    "T_PoetiqActionSettings", bound=BasePoetiqActionSettings
)
T_SplitActionSettings = TypeVar("T_SplitActionSettings", bound=BaseSplitActionSettings)
T_SetupSettings = TypeVar("T_SetupSettings", bound=BaseSetupSettings)
