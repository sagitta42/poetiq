from abc import abstractmethod
from pathlib import Path

from poetiq.exceptions import PoetiqException
from poetiq.setup.env_settings import EnvSettingsSetup
from poetiq.setup.gitignore import GitignoreSetup
from poetiq.settings.template import T_TemplateSettings
from poetiq.logger import logg

from poetiq.setup.base.poetry import BasePoetrySetup
from poetiq.utils.path import Dir, File
from poetiq.utils.toml import TomlHandler
from poetiq.utils.tree import display
from poetiq.utils.misc import POETIQ_LINK


class BaseTemplate(BasePoetrySetup[T_TemplateSettings]):
    """
    General template setup.

    Included functionalities setup:
        - gitignore
        - VSCode

    Repository setup:
        - source files
        - README

    Operations
        - repository init (git, poetry)
        - repository setup
        - repository update

    Repository update: updating existing template with poetiq updates.
    """

    def __init__(self, path: Path | None, settings: T_TemplateSettings) -> None:
        """
        Initialize template setup with given settings.

        path (Path): path in which to do the setup.
            Default (None): package name
        """
        self.name = settings.name

        template_path = path or Path(self.name)

        super().__init__(template_path, settings, core=True)

        self._inner_name = self.name.replace("-", "_")

        # self._git_auto = Git(self._path_to_resources.parent.parent)

        self._gitignore = GitignoreSetup(self.path)
        self._env_settings_setup: EnvSettingsSetup | None = None

        self._path_to_poetiq_toml = self.path / "poetiq.toml.template"
        self._poetiq_toml_handler = TomlHandler(self._path_to_poetiq_toml)

    @property
    def title(self) -> str:
        return f"{super().title}: {self.name}"

    def launch(self) -> None:
        """
        Template launch action: init template
        Add poetiq line to readme at the end of setup.
        """
        if Dir(self.path).exists_and_non_empty():
            raise PoetiqException(
                f"{self.name} exists and non-empty! Change name or (re)move existing packge; or run poetiq update inside existing package if you wish to update it."
            )

        super().launch()

        logg.info(f"Template setup DONE", header=True)

    def update(self):
        """
        (Safe) Update existing template.

        Attempt an update, switch to original branch in case of fail.
        """
        self._check_for_changes()

        try:
            current_branch = self._git.get_active_branch()
        except PoetiqException as e:
            raise PoetiqException(f"Attempting to determine current branch, {str(e)}")
        logg.info(f"Active branch: {current_branch}")

        try:
            self._update(current_branch)
        except Exception as e:
            self._git.run("switch", current_branch)
            raise e

    def _update(self, current_branch: str):
        """
        Update existing template.

        Switch to branch dev-poetiq-update.
            If does not exist, create starting from first repo commit.
            NOTE: assumes the first commit is the poetiq template commit.
            NOTE: this branch is expected to be reserved for poetiq updates.
        Run setup.
        Commit updates.
        Switch to current branch.
        Merge dev-poetiq-update.
        """
        update_branch = "dev-poetiq-update"
        if not self._git.branch_exists(update_branch):
            first_commit = self._git.get_first_commit()
            logg.info(
                f"Creating {update_branch} starting from first commit {first_commit}"
            )
            self._git.run("branch", update_branch, first_commit)

        self._git.run("switch", update_branch)

        self.setup()

        # FIXME: correctly get poetiq commits
        # last_poetiq_commit = self._git_auto.get_last_commit()
        # last_poetiq_commit_message = self._git_auto.get_commit_message(
        # last_poetiq_commit
        # )
        # message = f"{self._poetiq_link} update\ncommit: {last_poetiq_commit}\nmessage: {last_poetiq_commit_message}"

        self._add_poetiq_line()
        message = f"latest {POETIQ_LINK} update"
        self._git.commit_all(message)

        self._git.run("switch", current_branch)
        self._git.run("merge", update_branch)

    def setup(self) -> None:
        """
        Main setup.

        Set up standard .gitignore.
        Set up source files.
        Set up pydantic-settings class for if requested.
        Set up .vscode launch and settings.
        Set up pyproject.toml.
        Set up poetiq.toml.template.
        """
        self._gitignore.setup()

        super().setup()

        self.setup_source_files()

        if self._env_settings_setup is not None:
            self._env_settings_setup.setup()
        self._vscode.setup()

        self.setup_pyproject()
        self._setup_poetiq_toml()

    def setup_dependencies(self):
        super().setup_dependencies()

        self._poetry_add("pydantic")

    def setup_readme(self):
        """
        Set up README.md

        Set up fresh readme.
        Use package name as title.
        Include template if exists.
        """
        super().setup_readme()
        logg.info(f"- creating {self._type} README.md")

        self._readme.clean()
        self._readme.add_new_section(self.name, header=1)

        readme_template_path = self._templates.get_filepath("README.md")
        if readme_template_path.exists():
            self._readme.update_from_template(readme_template_path)

    def setup_pyproject(self):
        """
        Set up pyproject.toml.

        Set up poetiq section in pyproject.toml.
        """
        self._pyproject_handler.read()
        self._pyproject_handler.add_section(
            "tool.poetiq", self._settings.core_settings()
        )
        self._pyproject_handler.write()

    def display(self, suggest_commit: str | None = None):
        """
        Display the template via tree.
        """
        logg.info(self.name)
        display(self.path)

    def _add_poetiq_line(self):
        self._readme.add_poetiq_line(prep="with")

    def _setup_poetiq_toml(self):
        """
        Setup poetiq.toml template if does not exist.

        Set up poetiq.toml.template file.
        Add poetiq.toml to .gitignore.
        """
        if not self._path_to_poetiq_toml.exists():
            self._poetiq_toml_handler.add_section(
                "dependency-groups",
                {
                    "local": [
                        "my-package @ /path/to/my-package",
                        "python-module @ /path/to/my/fork/of/python-module",
                    ]
                },
            )
            self._poetiq_toml_handler.write()

        File(self.path / ".gitignore").add_new_line("poetiq.toml", prepend=True)

    @abstractmethod
    def setup_source_files(self):
        """
        Set up source files.
        """
        pass

    def _commit_message(self, mod_type: str) -> str:
        ret = f"template {mod_type} with {POETIQ_LINK}"
        return ret
