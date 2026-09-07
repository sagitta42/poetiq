import os
from pathlib import Path
import subprocess

from poetiq.utils.command_runner import BaseCommandRunner
from poetiq.utils.misc import find_line, find_line_startswith
from poetiq.utils.pip import Pip
from poetiq.utils.toml import PyProjectHandler
from poetiq.utils.venv import Venv


class Poetry(BaseCommandRunner):
    def __init__(self, path: Path | None, venv_path: Path | None = None) -> None:
        super().__init__(path, command="poetry")

        self._venv = Venv(venv_path or self.path)
        self._pip = Pip(self.path)
        self._pyproject = PyProjectHandler(self.path)
        self._pyproject.read()

    def init_basic(self, name: str | None = None):
        """
        Basic poetry init with no structure.
        """
        package_name = name or self.path.stem
        self.run(
            "init",
            "--no-interaction",
            "--name",
            package_name,
            "--description",
            "",
        )

    def add(self, *args, **kwargs):
        self.run("add", *args, **kwargs)

    def is_package_mode(self) -> bool:
        """
        Determine if current pyproject is in package mode.
        """
        project = self._pyproject.get_section("project")
        tool_poetry = self._pyproject.get_section("tool.poetry")

        package_mode = project.get("package-mode", None)
        if package_mode is None:
            package_mode = tool_poetry.get("package-mode", True)

        return package_mode

    def run(self, *args, **kwargs) -> list[str] | None:
        """
        Run a poetry command.

        A poetry call is outside of a venv of the project.
        It is called from the same environment in which poetiq is installed and being used.

        Run command, and in case error is captured, rerun with capture output in order to analyze the error.
        Handle externally-managed-environment: run pip command in current venv
        Then rerun the original command.
        """
        try:
            return self._run(*args, **kwargs)
        except subprocess.CalledProcessError:
            try:
                return self._run(
                    *args, info=False, capture_output=True, text=True, **kwargs
                )
            except subprocess.CalledProcessError as e:
                if "externally-managed-environment" in e.stdout:
                    self._rerun_poetry_pip(e)
                    self.run(*args, **kwargs)
                else:
                    raise e

    def _run(self, *args, info: bool = True, **kwargs) -> list[str] | None:
        return super().run(
            *args,
            info=info,
            env={
                **os.environ,
                "POETRY_VIRTUALENVS_CREATE": "false",
                "VIRTUAL_ENV": self._venv.venv,
            },
            **kwargs,
        )

    def _rerun_poetry_pip(self, e: subprocess.CalledProcessError):
        """
        Rerun poetry's attempt to run pip (uninstall).

        Hitting externally-managed-environment with /usr/bin/python.

        Find each EnvCommandError chunk in stdout relating to externally-managed-environment.
        Locate pip command.
        Rerun pip command using local venv pip.
        """
        original_error_lines: list[str] = [l.strip() for l in e.stdout.split("\n")]
        error_lines = original_error_lines[:]

        flag = True
        while flag:
            idx_env_error = find_line(error_lines, "EnvCommandError")
            idx_ext_managed = find_line(
                error_lines, "error: externally-managed-environment"
            )
            if idx_env_error is None or idx_ext_managed is None:
                flag = False
                continue

            env_error_lines = error_lines[idx_env_error:idx_ext_managed]
            command_line = find_line_startswith(env_error_lines, "Command")
            assert command_line is not None, "Command line not found in EnvCommandError"
            command_list_str = (
                command_line.removeprefix("Command")
                .lstrip()
                .removeprefix("[")
                .split("]")[0]
            )

            command_list = eval(f"[{command_list_str}]")
            pip_command_list = command_list[3:]
            self._pip.run(*pip_command_list)

            error_lines = error_lines[idx_ext_managed:]
