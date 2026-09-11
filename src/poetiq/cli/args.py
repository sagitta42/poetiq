# TODO: OOP encalsulate duplications -> pydantic-argparse
import argparse
from typing import Any, Type

from poetiq.settings.base import BaseActionSettings


def add_bool(
    parser: argparse.ArgumentParser,
    name: str,
    help: Type[BaseActionSettings],
    exclusive: bool = False,
    optional: bool = True,
):
    """
    Add bool argument.

    exclusive: exclusive to these settings

    optional (bool): if not provided, defaults to False
    """

    parser.add_argument(
        f"--{name}",
        action="store_true",
        default=False if optional else None,
        help=help.description(name, exclusive=exclusive),
    )


def add_str(
    parser: argparse.ArgumentParser,
    name: str,
    help: Type[BaseActionSettings],
    optional: bool,
    flag: bool = True,
    informative: bool = False,
    exclusive: bool = False,
    choices: list[Any] | None = None,
    **kwargs,
):
    """
    Add string argument.

    optional (bool): if not provided, defaults to default
    flag: add -- i.e. --name keyword argument
    exclusive (bool): this argument is exclusive to the given type of settings
    informative ( bool): (applies to flag only) if just --flag is provided with no option, assume const value
    """
    arg_name = name
    if flag:
        arg_name = f"--{arg_name}"

    flag_kwargs = {}
    if flag:
        flag_kwargs["required"] = not optional

    parser.add_argument(
        arg_name,
        type=str,
        default=help.default(name) if optional else None,
        choices=choices or help.options(name),
        nargs="?" if (flag and informative) or (not flag and optional) else None,
        const=help.const(name) if flag and informative else None,
        help=help.description(name, exclusive=exclusive),
        **flag_kwargs,
        **kwargs,
    )
