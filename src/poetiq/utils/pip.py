import os
from pathlib import Path

from pydantic import BaseModel

from poetiq.utils.command_runner import BaseCommandRunner
from poetiq.logger import logg
from poetiq.utils.misc import list_as_args
from poetiq.utils.venv import Venv


class PackageInfo(BaseModel):
    name: str
    version: str | None
    source: str | None


def get_package_info(pip_str: str, split_str: str) -> tuple[str, str]:
    """
    Get package information splitting dependency string by given split string.

    E.g. package==1.2.3, package @ path
    """
    package, info = [component.strip() for component in pip_str.split(split_str)]
    return package, info


def get_package_source(pip_str: str) -> tuple[str, str]:
    """
    Extract package name and source from "package @ source" pip string.

    Remove final "/" in filepath.
    """
    package, path = get_package_info(pip_str, " @ ")
    path = path.removesuffix("/")
    return package, path


def get_egg_package(pip_str: str) -> tuple[str, str]:
    """
    Extract package name and source from "-e ... egg=package" pip string.

    Example:
    -e git+https://github.com/user/package-name.git@77c73b422d3326d14c1e930239c00a3ce460bc78#egg=package_name
    """
    source, package = pip_str.split("#egg=")
    source = source.removeprefix("-e").lstrip()
    package = package.replace("_", "-")
    return package, source


def get_package_version(pip_str: str) -> tuple[str, str]:
    """
    Extract package version from "package==1.2.3" pip string.
    """
    ret = get_package_info(pip_str, "==")
    return ret


class Pip(BaseCommandRunner):
    """
    Get pip information.

    Get information from pip freeze.
    """

    def __init__(self, path: Path | None) -> None:
        super().__init__(path)

        self._venv = Venv(self.path)

    def freeze(self) -> list[str]:
        """
        Get output of pip freeze in list format.
        """
        ret = self.run("freeze", check_output=True)
        assert ret is not None
        return ret

    def get_package_info(self, name: str) -> PackageInfo | None:
        """
        Get info of pip package, if present in pip freeze.
        """
        all_pip_packages = self.get_all_packages()
        for package in all_pip_packages:
            if package.name == name:
                return package

        return None

    def get_all_packages(self) -> list[PackageInfo]:
        """
        Get package infos from pip freeze.

        Version if package==1.2.3.
        Path if package @ path (preserves file:// prefix)
        """
        pip_packages = self.freeze()

        ret = []
        for package_info in pip_packages:
            logg.debug(package_info)
            if package_info.startswith("-e") and "#egg=" in package_info:
                name, source = get_egg_package(package_info)
            elif "@" in package_info:
                name, source = get_package_source(package_info)
                version = None
            elif "==" in package_info:
                name, version = get_package_version(package_info)
                source = None
            else:
                raise NotImplementedError(
                    f"Could not parse pip freeze format {package_info}! Checking for @ or ==; unrecognized"
                )

            ret.append(PackageInfo(name=name, version=version, source=source))

        return ret

    def run(self, *args, external: bool = False, **kwargs) -> list[str] | None:
        """
        Run pip command.

        Pip command is normally envoked from the venv of the path/project.
        Exception: global environment management during poetry actions.
        """
        run = super().run if external else self._venv.run
        return run("pip", *args, **kwargs)
