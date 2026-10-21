import os
from pathlib import Path
import subprocess

from poetiq.action.install import InstallAction
from poetiq.settings.poetiq_action import InstallSettings
from poetiq.setup.env_settings import EnvSettingsSetup
from poetiq.setup.logger import LoggerSetup
from poetiq.setup.progress_bar import ProgressBarSetup
from poetiq.settings.setup import DotenvSettings, LoggerSettings, ProgressBarSettings
from poetiq.settings.template import PackageTemplateSettings
from poetiq.template.base import BaseTemplate
from poetiq.utils.path import File
from poetiq.utils.template import TemplateLocation


class PackageTemplate(BaseTemplate[PackageTemplateSettings]):
    """
    Package template setup.
    """

    def __init__(self, path: Path | None, settings: PackageTemplateSettings) -> None:
        super().__init__(path, settings)

        src_subdir = Path("src") / self._inner_name
        self._path_to_src: Path = self.path / src_subdir

        # TODO: unify for internal items, use builder with core=False
        self._logger_setup = LoggerSetup(
            self.path, LoggerSettings(subfolder=src_subdir), core=False
        )

        self._env_settings_setup = (
            EnvSettingsSetup(
                self.path, DotenvSettings(subfolder=src_subdir), core=False
            )
            if self._settings.settings
            else None
        )

        self._progressbar_setup: ProgressBarSetup | None = (
            ProgressBarSetup(
                self.path, ProgressBarSettings(subfolder=src_subdir), core=False
            )
            if self._settings.progressbar
            else None
        )

    def setup(self):
        """
        Package template setup.

        In addition to base template setup:
            Set up .env template
            Set up tests (conftest, dummy test)
            Set up Logger
            Set up ProgressBar if requested
        """
        super().setup()

        self.setup_dotenv_template()
        self.setup_tests()

        self._logger_setup.setup()

        if self._progressbar_setup is not None:
            self._progressbar_setup.setup()

        self.setup_main_script()

        install_action = InstallAction(self.path, InstallSettings())
        install_action.launch()

    def _poetry_init(self):
        """
        Initialize package with poetry.

        Run "poetry new" from within path if exists (and empty).
        Standard setup with src/package_name structure.
        Run poetry from same environment from which poetiq is being called
            (not poetry from project's venv - does not exist yet)
        """
        poetry_args = ["poetry", "new"]

        if self.path.exists():
            package = "."
            path = self.path
        else:
            package = self.name
            path = self.path.parent

        subprocess.run(poetry_args + [package], cwd=path)

    def setup_source_files(self):
        """
        Set up source files.

        Create a dummy source file (convenient for tests).
        Add dummy function to __init__.py.
        Set up MyBaseModel if requested.
        Set up __main__.py enabling python -m and CLI package running.
        Set up __version__.py reading from pyproject.toml.
        Set up py.typed enabling package imports.
        """

        self._templates.copy("foo.py", package_path=self._path_to_src)

        init_file = File(self._path_to_src / "__init__.py")
        init_file.add_new_line(
            f"from {self._inner_name}.foo import is_answer as is_answer"
        )

        if self._settings.my_base_model:
            source_file_path = self._templates.copy(
                "base_model.py",
                package_path=self._path_to_src,
                template_location=TemplateLocation.common_ass,
            )
            self._replace_package_placeholder(source_file_path)

        for src_file in ["__main__.py", "__version__.py"]:
            path_to_file = self._templates.copy(
                src_file, package_path=self._path_to_src
            )
            self._replace_package_placeholder(path_to_file)

        init_file.add_new_line(
            f"from {self._inner_name}.__version__ import __version__", prepend=True
        )

        self._create_source_file("py.typed")

    def setup_dependencies(self):
        super().setup_dependencies()

        self._poetry_add("pytest", "dev")

    def setup_readme(self):
        """
        Set up README.md.

        Set up README from template.
        Replace instances of $PACKAGE and $package.
        """
        super().setup_readme()

        self._replace_package_placeholder(self._readme.path_to_readme)

    def setup_tests(self):
        """
        Set up tests.

        Create conftest.py that allows testing in dev mode without installing the package.
        Create dummy test corresponding to the dummy source file.
        Add pytest as dev dependency.
        """
        path_to_tests: Path = self.path / "tests"
        path_to_configs = path_to_tests / "configs"
        os.makedirs(path_to_configs, exist_ok=True)

        conftest_filepath = self._templates.copy("conftest.py", path_to_tests)
        self._replace_package_placeholder(conftest_filepath)

        self._templates.copy("test_case.json", package_path=path_to_configs)

        test_unit_filepath = self._templates.copy(
            "test_unit.py", package_path=path_to_tests
        )
        self._replace_package_placeholder(test_unit_filepath)

    def setup_main_script(self):
        """
        Set up main script in pyproject.toml based on __main__.py
        """
        self._pyproject_handler.add_section(
            "project.scripts", {self.name: f"{self._inner_name}.__main__:main"}
        )
        # TODO: consistency between whether each singular add writes as in some utils
        # VS must call final write
        self._pyproject_handler.write()

    def _create_source_file(self, filepath: str | Path):
        """
        Create empty source file with given name or path.
        """
        f = open(self._path_to_src / filepath, "w")
        f.close()

    def _replace_package_placeholder(self, filepath: Path):
        """
        Replace package placeholer in file in given file.

        Replace $package with package-name
        Replace $PACKAGE with package_name.
        """
        File(filepath).replace_str("$package", self.name)
        File(filepath).replace_str("$PACKAGE", self._inner_name)
