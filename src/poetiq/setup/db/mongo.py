from pathlib import Path

from poetiq.enums import DBType
from poetiq.setup.db.base.docker import DockerDBSetup
from poetiq.settings.setup import DBSettings
from poetiq.utils.db import HostedDBEnvVars


class MongoDBSetup(DockerDBSetup[HostedDBEnvVars]):
    def __init__(
        self,
        path: Path,
        env_vars: HostedDBEnvVars,
        settings: DBSettings = DBSettings(db_type=DBType.mongo),
        core: bool = False,
    ) -> None:
        super().__init__(path, env_vars, settings, core)

    def setup_db(self):
        super().setup_db()

        # TODO: independent setup here

    def setup_dependencies(self) -> None:
        super().setup_dependencies()

        self._poetry_add("pymongo")

    def setup_readme(self):
        self._readme.add_new_section("MongoDB", header=3)
        super().setup_readme()
