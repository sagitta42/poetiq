from poetiq.setup.db.base.docker import DockerDBSetup
from poetiq.setup.db.base.sql import DBSqlSetup
from poetiq.utils.db import HostedSqlDBEnvVars


class PsqlDBSetup(DBSqlSetup[HostedSqlDBEnvVars], DockerDBSetup[HostedSqlDBEnvVars]):
    """
    PSQL database setup.
    """

    def setup_dependencies(self):
        """
        Set up dependencies for PSQL functionality.

        psycopg[binary] is needed for app engine connection and alembic migrations.
        """
        super().setup_dependencies()

        self._poetry_add("psycopg[binary]")
