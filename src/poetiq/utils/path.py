import os
from pathlib import Path
import shutil

from poetiq.logger import logg


class PathUtil:
    def __init__(self, path: Path) -> None:
        self._path = path


class Dir(PathUtil):
    def exists_and_non_empty(self) -> bool:
        """
        Check if path exists and is not empty
        """
        ret = self._path.exists() and len(os.listdir(self._path)) > 0
        return ret


class File(PathUtil):

    @property
    def lines(self) -> list[str]:
        ret = []
        if self._path.exists():
            with open(self._path) as f:
                ret = [l.rstrip() for l in f.readlines()]

        return ret

    def add_new_line(self, line: str, prepend: bool = False):
        """
        Add line to file if it does not contain it.
        """
        if not self.has_line(line):
            self._add_line(line, prepend)

    def remove_line(self, line: str):
        """
        Remove all instances of line in file.
        """
        new_lines = [l for l in self.lines if l != line.rstrip()]
        self._write(new_lines)

    def replace_str(self, str_original: str, str_replace: str):
        """
        Replace given string with another in file.

        Replaces all instances of given string.
        """
        new_lines = [line.replace(str_original, str_replace) for line in self.lines]
        self._write(new_lines)

    def has_line(self, line: str) -> bool:
        """
        Check if file has given line
        """
        ret = line.rstrip() in self.lines
        return ret

    def _add_line(self, line: str, prepend: bool):
        """
        Add line to file.

        prepend (bool): add to top of file instead of bottom
        """
        new_line = f"{line}"
        updated_lines = [new_line] + self.lines if prepend else self.lines + [new_line]
        self._write(updated_lines)

    def _write(self, lines: list[str]):
        """
        Write given lines to file.

        Expects lines without the end of line characters.
        """
        with open(self._path, "w") as f:
            f.writelines([f"{l}\n" for l in lines])


def copy_file(file_to_copy: Path, copy_dest: Path):
    logg.info(f"Copying {file_to_copy} -> {copy_dest}")
    shutil.copy(file_to_copy, copy_dest)
