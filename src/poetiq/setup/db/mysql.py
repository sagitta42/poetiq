from poetiq.setup.db.base.docker import DockerDBSetup
from poetiq.setup.db.base.sql import DBSqlSetup
from poetiq.utils.db import HostedSqlDBEnvVars


class MySqlDBSetup(DBSqlSetup[HostedSqlDBEnvVars], DockerDBSetup[HostedSqlDBEnvVars]):
    """
    MySQL database setup.
    """

    def setup_dependencies(self):
        """
        Set up dependencies for MySQL functionality.

        pymysql is needed for app engine connection and alembic migrations.
        """
        super().setup_dependencies()

        self._poetry_add("pymysql")
