from poetiq.action.base import BaseSplitPoetiqAction
from poetiq.logger import logg
from poetiq.settings.poetiq_action import AddSettings
from poetiq.utils.package import Package


class AddAction(BaseSplitPoetiqAction[AddSettings]):

    def launch(self) -> None:
        """
        Launch poetry add.

        Add to pyproject auto-detecting git+ or ssh://.
        If split, add to pyproject.toml in the specified directory.
        If local, add local path of dependency to poetiq.toml.
        """
        if self._settings.local is None:
            self._add_pyproject()
        else:
            self._add_poetiq()

    def _add_pyproject(self):
        """
        Perform standard poetry add to a pyproject.toml.

        Assumes https links start with https:// (e.g. GitHub) and only prepends git+
        Assumes if neither https nor ssh at start of link, that it is an ssh one missing the prepend.


        """
        package = Package(name="", version=None, source=self._settings.package)

        poetries = self._get_poetries_of_interest()
        assert (
            len(poetries) == 1
        ), "poetiq add wants single poetry - main one or single split DIR"
        poetry = poetries[0]

        logg.info(f"Adding to {poetry.path}...", poetiq=True)
        poetry.add(package.source_str)

    def _add_poetiq(self):
        dep_section = "dependency-groups"

        self._poetiq_toml.add_section(dep_section)
        if not "local" in self._poetiq_toml.get_section(dep_section):
            self._poetiq_toml.add_section(dep_section, {"local": []})

        entry = f"{self._settings.package} @ {self._settings.local}"
        self._poetiq_toml._toml_dict[dep_section]["local"].append(entry)
        logg.info(f"Added dependency to {self._toml_name}")
        logg.info(entry, poetiq=True)
        self._poetiq_toml.write()
