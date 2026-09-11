from abc import abstractmethod
import enum
from typing import Any, Optional, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field
from pydantic.fields import FieldInfo

from poetiq.enums import ActionType


class BaseActionSettings(BaseModel):
    """
    Base class for settings for any action.

    Adaptor utils to argparse.
    """

    model_config = ConfigDict(extra="ignore")
    type: ActionType = Field(description="Action type; discriminator")

    @classmethod
    def options(cls, arg: str) -> list | None:
        field = cls._get_field(arg)
        field_type = cls._get_arg_type(field)
        assert field_type is not None
        if issubclass(field_type, enum.Enum):
            ret = [item.value for item in field_type]
            return ret
        return None

    @classmethod
    def default(cls, arg: str) -> Any:
        ret = cls._get_field(arg).default
        if isinstance(ret, enum.Enum):
            ret = ret.value
        return ret

    @classmethod
    def alias(cls, arg: str) -> str:
        ret = cls._get_field(arg).alias or arg
        return ret

    @classmethod
    def description(cls, arg: str, exclusive: bool = False) -> str:
        """
        Field description util for argparse.

        exclusive: add note that it is exclusive for this type of template.
        """
        ret = cls._get_field(arg).description
        assert ret is not None
        if exclusive:
            template_type = cls.default("type")
            ret += f" ({template_type} only)"
        return ret

    @classmethod
    def const(cls, arg: str) -> str:
        """
        Constant value.

        Default value = setting not mentioned
        Const value = setting mentioned without specifying value
        """
        return cls.default(arg)

    @classmethod
    def _get_arg_type(cls, field: FieldInfo) -> type:
        """
        Get arg type from annotation.

        Extract real type from type union to cover Optional[type] case.
        """
        # TODO: validator
        assert field.annotation is not None
        if get_origin(field.annotation) is Union:
            types = get_args(field.annotation)
            real_types = [tp for tp in types if not tp is type(None)]
            # TODO: validator
            assert len(real_types) == 1
            return real_types[0]
        return field.annotation

    @classmethod
    def _get_field(cls, arg: str) -> FieldInfo:
        return cls.model_fields[arg.replace("-", "_")]


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
    """

    split: Optional[str] = Field(default=None, description="Split directory")

    @property
    def split_requested(self) -> bool:
        return self.split is not None

    @classmethod
    def const(cls, arg: str) -> str:
        """
        Const value for --split flag

        --split flag not provided -> default
        --split flag provided with no argument -> const

        const = "" = all split directories
        """
        if arg == "split":
            return ""
        return super().const(arg)


class BaseSetupSettings(BaseActionSettings):
    """
    Base class for settings for any type of setup.
    """

    type: ActionType = Field(description="Setup type")
    no_commit: bool = Field(default=False, description="Do not commit changes")


T_ActionSettings = TypeVar("T_ActionSettings", bound=BaseActionSettings)
T_PoetiqActionSettings = TypeVar(
    "T_PoetiqActionSettings", bound=BasePoetiqActionSettings
)
T_SplitActionSettings = TypeVar("T_SplitActionSettings", bound=BaseSplitActionSettings)
T_SetupSettings = TypeVar("T_SetupSettings", bound=BaseSetupSettings)
