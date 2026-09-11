import argparse
from pathlib import Path
import sys
from poetiq.cli.cli import (
    Subparser,
    add_microfunctionality_arguments,
    add_template_arguments,
)
from poetiq.cli.poetiq_action import (
    add_install_arguments,
    add_poetiq_add_arguments,
    add_poetiq_lock_arguments,
)
from poetiq.core import launch_action, update
from poetiq.exceptions import PoetiqException
from poetiq.logger import logg
from poetiq.enums import ActionType
from poetiq.utils.poetry import Poetry


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    install_subparser = subparsers.add_parser(
        Subparser.install.value, help=Subparser.install.descr()
    )
    add_install_arguments(install_subparser)

    add_subparser = subparsers.add_parser(
        Subparser.add.value, help=Subparser.add.descr()
    )
    add_poetiq_add_arguments(add_subparser)

    lock_subparser = subparsers.add_parser(
        Subparser.lock.value, help=Subparser.lock.descr()
    )
    add_poetiq_lock_arguments(lock_subparser)

    subparsers.add_parser(Subparser.init.value, help="basic no-interaction init")

    new_template_subparser = subparsers.add_parser(
        Subparser.new.value, help="create new template"
    )
    add_template_arguments(new_template_subparser)

    subparsers.add_parser(
        Subparser.update.value,
        help="update current template as is with new poetiq updates",
    )

    micro_functionality_subparser = subparsers.add_parser(
        Subparser.setup.value, help="setup functionality in existing repo/directory"
    )
    add_microfunctionality_arguments(micro_functionality_subparser)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    logg.debug(vars(args))

    settings_args = vars(args).copy()
    subparser_command = settings_args.pop("command")
    if subparser_command in ActionType:
        command = ActionType(subparser_command)
        settings_args["type"] = subparser_command
    else:
        command = Subparser(subparser_command)

    # TODO: attach exec() to parser, define elsewhere
    try:
        if command == Subparser.init:
            poetry = Poetry(Path.cwd())
            poetry.init_basic()
        elif command == Subparser.update:
            update()
        else:
            launch_action(settings_args)

    except PoetiqException as e:
        logg.error(str(e))
        return


if __name__ == "__main__":
    main()
