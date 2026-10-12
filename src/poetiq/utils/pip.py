from pathlib import Path


from poetiq.utils.command_runner import BaseCommandRunner
from poetiq.utils.package import Package, PackageName
from poetiq.logger import logg
from poetiq.utils.venv import Venv


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

    def get_package(self, name: PackageName) -> Package | None:
        """
        Get package from pip freeze (if present).
        """
        all_pip_packages = self.get_all_packages()
        for package in all_pip_packages:
            if package.name == name:
                return package

        return None

    def get_all_packages(self) -> list[Package]:
        """
        Get all packages from pip freeze.
        """
        pip_packages = self.freeze()

        ret = []
        for package_str in pip_packages:
            logg.debug(package_str)
            package = Package.from_package_str(package_str)

            if package.source is not None and any(package.source.startswith(prefix) for prefix in ["file://", "git+"]):
                package.name = package.name.replace("_", "-")

            ret.append(package)

        return ret

    def run(self, *args, external: bool = False, **kwargs) -> list[str] | None:
        """
        Run pip command.

        Pip command is normally envoked from the venv of the path/project.
        Exception: global environment management during poetry actions.
        """
        run = super().run if external else self._venv.run
        return run("pip", *args, **kwargs)
