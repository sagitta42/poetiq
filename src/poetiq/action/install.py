import enum
from functools import cached_property
from pathlib import Path
import subprocess


from poetiq.action.base import BaseSplitPoetiqAction
from poetiq.exceptions import PoetiqException

from poetiq.logger import logg
from poetiq.settings.poetiq_action import InstallSettings
from poetiq.utils.pip import PackageInfo, Pip, get_package_source


class InstallSource(enum.StrEnum):
    local = "local"
    pyproject = "pyproject"


class InstallAction(BaseSplitPoetiqAction):
    """
    Install functionalities on top of standard poetry.

    Uses information in poetiq.toml file on dual dependencies.
    Checks information in pyproject.toml for install type.
    """

    def __init__(self, path: Path, settings: InstallSettings) -> None:
        super().__init__(path, settings)

        self._pip = Pip(self.path)

    def launch(self):
        """
        Run poetiq install action.

        Run "poetry lock" automatically if poetry.lock determined to be too old.
        Run poetry install handling dual dependencies.

        If local flag was given in settings, perform local install:
            - perform full poetry install if no specific package was requested
            - uninstall dual dependencies if they do not already point to local path
            - install based on paths from poetiq.toml

        Otherwise perform install based on pyproject.toml:
            - uninstall dual dependencies
                TODO: check if already points to pyproject and skip
            - install based on pyproject.toml (i.e. standard poetry install)

        Perform dual package treatment on given package name; or all if none are given.
        """
        if self._settings.local and not self._has_dual_packages():
            logg.warning(
                f"Local install requested but no dual dependencies found in {self._toml_name}"
            )

        if self._has_dual_packages() and not self._settings.local:
            self._uninstall_dual_packages(InstallSource.pyproject)

        if self._settings.package is None:
            self._full_poetry_install()
        elif not self._settings.local:
            self._pip.run("install", self._settings.package, info=True)

        if self._has_dual_packages() and self._settings.local:
            self._uninstall_dual_packages(InstallSource.local)
            for package in self._get_local_packages_of_interest():
                self._pip.run("install", package.source, info=True)

    def _full_poetry_install(self):
        """
        Perform full poetry install.

        Determine poetries of interest (current dir, given split dir, all split dir).
        Perform poetry install with each poetry of interest.
        Run poetry lock automatically if poetry reports that pyproject.toml
            changed significantly since poetry.lock was last generated.
        TODO: flag to create/update (split) poetry.lock.prod file(s)
        """

        poetries = self._get_poetries_of_interest()

        for poetry in poetries:
            poetry_args = ["install"]

            logg.info(f"Installing from {poetry.path}...", poetiq=True)
            try:
                poetry.run(*poetry_args, check=True)
            except subprocess.CalledProcessError as e:
                if "poetry.lock" in e.stderr:
                    logg.info(f"-> Running poetry lock", poetiq=True)
                    poetry.run("lock")
                    poetry.run(*poetry_args, check=True)

    def _has_dual_packages(self) -> bool:
        """
        Determine if packages with dual dependencies are present.
        """
        return len(self._all_local_packages) > 0

    def _uninstall_dual_packages(self, install_source: InstallSource):
        """
        Uninstall dual packages.

        Uninstall dual packages of interest listed as local in poetiq.toml.
        Skip if package is not present in pip freeze.

        Local install: do not perform uninstall if package already points to same install path in pip freeze.
        Pyproject install: do not perform uninstall if package does NOT point to local path install source.
        """
        for local_package in self._get_local_packages_of_interest():
            pip_freeze_info = self._pip.get_package_info(local_package.name)

            if pip_freeze_info is None:
                continue

            # NOTE: currently with package==1.2.3 source is None
            assert (
                pip_freeze_info.source is not None
                or pip_freeze_info.version is not None
            ), f"neither source nor version in pip freeze info on {local_package.name}"

            pip_source = (
                None
                if pip_freeze_info.source is None
                else pip_freeze_info.source.removeprefix("file://")
            )

            if install_source == InstallSource.local:
                if local_package.source == pip_source:
                    continue
                logg.info(f"{pip_freeze_info.source} -> {local_package.source}")
            elif install_source == InstallSource.pyproject:
                # TODO: compare to actual pyproject
                if pip_source != local_package.source:
                    continue

            logg.info(
                f"Replacing dual package {local_package.name} with {install_source} dependency",
                header=True,
            )

            self._pip.run("uninstall", local_package.name, "-y", info=True)

    def _get_local_packages_of_interest(self) -> list[PackageInfo]:
        """
        Get list of local packages of interest for install.

        All local packages if no specific package requested.
        """

        ret = (
            self._all_local_packages
            if self._settings.package is None
            else [self._local_package_map[self._settings.package]]
        )
        return ret

    @cached_property
    def _local_package_map(self) -> dict[str, PackageInfo]:
        ret = {package.name: package for package in self._all_local_packages}
        return ret

    @cached_property
    def _all_local_packages(self) -> list[PackageInfo]:
        """
        Get list of all local packages from poetiq toml.
        """
        poetiq_settings = self._poetiq_toml.get_section("dependency-groups")
        local_deps_items = poetiq_settings.get("local", [])
        ret = []
        for dep_str in local_deps_items:
            if not "@" in dep_str:
                raise PoetiqException(
                    f"Incorrect fromat in {self._toml_name} local dependency: {dep_str}! Use package @ path format"
                )
            package, path = get_package_source(dep_str)
            ret.append(PackageInfo(name=package, source=path, version=None))
        return ret
