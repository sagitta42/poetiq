from poetiq.action.base import BaseSplitPoetiqAction
from poetiq.logger import logg
from poetiq.settings.poetiq_action import LockSettings
from poetiq.utils.path import copy_file


class LockAction(BaseSplitPoetiqAction[LockSettings]):
    def launch(self) -> None:
        """
        Launch poetry lock.

        Run poetry lock.
        If split, run in all directories in poetiq.toml or the specified one.
        """
        poetries = self._get_poetries_of_interest()
        for poetry in poetries:
            logg.info(f"Updating poetry.lock in {poetry.path}...", poetiq=True)
            poetry.run("lock")

            if self._settings.prod:
                copy_file(poetry.path / "poetry.lock", poetry.path / "poetry.lock.prod")
