import enum
from functools import cached_property
from pathlib import Path
import subprocess


from poetiq.action.base import BaseSplitPoetiqAction
from poetiq.exceptions import PoetiqException

from poetiq.logger import logg
from poetiq.settings.poetiq_action import InstallSettings
from poetiq.utils.package import Package, PackageName
from poetiq.utils.pip import Pip


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
            self._install_package_from_pyproject(self._settings.package)

        if self._has_dual_packages() and self._settings.local:
            self._uninstall_dual_packages(InstallSource.local)
            for package in self._get_packages_of_interest(InstallSource.local):
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

    def _install_package_from_pyproject(self, package_name: PackageName):
        """
        Install given package according to pyproject.toml dependency source.
        """
        package = self.package_map[InstallSource.pyproject][package_name]
        self._pip.run("install", package.source_str, info=True)

    def _has_dual_packages(self) -> bool:
        """
        Determine if packages with dual dependencies are present.
        """
        return len(self.all_local_packages) > 0

    def _uninstall_dual_packages(self, install_source: InstallSource):
        """
        Uninstall dual packages.

        Uninstall dual packages of interest listed as local in poetiq.toml.
        Skip if package is not present in pip freeze.

        Local install: do not perform uninstall if pip freeze already shows the same install source
        Pyproject install: do not perform uninstall if package already points to the same install source as pyproject
        """

        for dual_package in self._get_packages_of_interest(InstallSource.local):
            logg.debug(f"Dual package {dual_package}")

            pip_package = self._pip.get_package(dual_package.name)
            logg.debug(f"Pip freeze: {pip_package}")

            if pip_package is None:
                continue

            # NOTE: currently with package==1.2.3 source is None
            assert (
                pip_package.source is not None or pip_package.version is not None
            ), f"neither source nor version in pip freeze info on {dual_package.name}"

            install_source_package = self.package_map[install_source][dual_package.name]
            logg.debug(f"{install_source} package: {install_source_package}")

            logg.debug(
                f"{install_source_package.source_str} VS {pip_package.source_str}"
            )
            if install_source_package.source_str == pip_package.source_str:
                continue

            logg.info(
                f"Replacing dual package {dual_package.name} with {install_source} dependency",
                header=True,
            )

            self._pip.run("uninstall", dual_package.name, "-y", info=True)

    def _get_packages_of_interest(self, install_source: InstallSource) -> list[Package]:
        """
        Get list of local/pyproject packages of interest.

        All local/pyproject packages if no specific package requested.
        """

        all_packages = self.package_map[install_source]
        ret = (
            list(all_packages.values())
            if self._settings.package is None
            else [all_packages[self._settings.package]]
        )
        return ret

    @cached_property
    def package_map(self) -> dict[InstallSource, dict[PackageName, Package]]:
        """
        Map of packages from local (poetiq.toml) and pyproject.toml dependencies.
        """
        ret = {
            InstallSource.local: {
                package.name: package for package in self.all_local_packages
            },
            InstallSource.pyproject: {
                package.name: package for package in self.all_pyproject_packages
            },
        }

        return ret

    @cached_property
    def all_local_packages(self) -> list[Package]:
        """
        Get list of all local packages from poetiq.toml.
        """
        poetiq_settings = self._poetiq_toml.get_section("dependency-groups")
        local_deps_items = poetiq_settings.get("local", [])
        ret = []
        for dep_str in local_deps_items:
            if not "@" in dep_str:
                raise PoetiqException(
                    f"Incorrect fromat in {self._toml_name} local dependency: {dep_str}! Use package @ path format"
                )

            package = Package.from_package_str(dep_str)
            assert package.source is not None, "package source is null in poetiq.toml"
            package.source = "file://" + package.source
            ret.append(package)
        return ret

    @cached_property
    def all_pyproject_packages(self) -> list[Package]:
        """
        Get list of all packages from pyproject.toml.

        Account for duplicates in case of split direcotres with multiple pyproject.toml.
        Check for package source consistency among split pyprojects.
        """
        poetries_of_interest = self._get_poetries_of_interest()

        duplicates_check: dict[PackageName, Package] = {}

        ret = []
        for poetry in poetries_of_interest:
            dependencies = poetry._pyproject.get_section("project")["dependencies"]
            for package_str in dependencies:
                package = Package.from_package_str(package_str)

                if package.name in duplicates_check:
                    if package != duplicates_check[package.name]:
                        raise NotImplementedError(
                            f"Package {package} has different source information in pyproject.toml files in split directories! Currently not supported"
                        )
                else:
                    duplicates_check[package.name] = package
                    ret.append(package)

        return ret
