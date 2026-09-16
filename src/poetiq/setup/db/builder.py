import enum
from pathlib import Path
from typing import Type

from poetiq.enums import DBType
from poetiq.setup.db.mongo import MongoDBSetup
from poetiq.setup.db.mysql import MySqlDBSetup
from poetiq.setup.db.psql import PsqlDBSetup
from poetiq.setup.db.base.single import SingleDBSetup
from poetiq.setup.db.sqlite import SQLiteSetup
from poetiq.logger import logg
from poetiq.settings.setup import DBSettings
from poetiq.utils.db import (
    DBEnvVars,
    EnvVar,
    HostedSqlDBEnvVars,
    HostedDBEnvVars,
    MySqlDBEnvVars,
    SqlDBEnvVars,
)


class DBSetupClass(enum.Enum):
    sqlite = SQLiteSetup
    psql = PsqlDBSetup
    mysql = MySqlDBSetup
    mongo = MongoDBSetup

    @classmethod
    def from_db_type(cls, db_type: DBType) -> Type[SingleDBSetup]:
        return cls[db_type.name].value


class DBPort(int, enum.Enum):
    psql = 5432
    mysql = 3306
    mongo = 27017

    @classmethod
    def from_db_type(cls, db_type: DBType) -> int:
        return cls[db_type.name].value


class DBEnvVarsClass(enum.Enum):
    sqlite = SqlDBEnvVars
    psql = HostedSqlDBEnvVars
    mysql = MySqlDBEnvVars
    mongo = HostedDBEnvVars

    @classmethod
    def from_db_type(cls, db_type: DBType) -> Type[DBEnvVars]:
        return cls[db_type.name].value


class BaseDatabaseStrEnum(enum.StrEnum):
    @classmethod
    def from_db_type(cls, db_type: DBType) -> str | None:
        return cls[db_type.name].value if db_type.name in cls.names() else None

    @classmethod
    def names(cls) -> list[str]:
        return cls._member_names_


class DatabasePrefix(BaseDatabaseStrEnum):
    mysql = "MYSQL"
    psql = "POSTGRES"

    @classmethod
    def with_var(cls, db_type: DBType, var: str) -> str:
        prefix = cls.from_db_type(db_type)
        ret = f"{prefix}_{var}"
        return ret


class BasePrefixEnvVar(BaseDatabaseStrEnum):
    @classmethod
    def from_db_type(cls, db_type: DBType) -> str | None:
        db_keyword = super().from_db_type(db_type)
        if db_keyword is None:
            return None
        ret = DatabasePrefix.with_var(db_type, db_keyword)
        return ret


class DatabaseEnvVar(BasePrefixEnvVar):
    mysql = "DATABASE"
    psql = "DB"


class DBSetupBuilder:
    """
    Builder for DB setup of specific DB type.
    """

    def build(self, path: Path, settings: DBSettings, core: bool) -> SingleDBSetup:
        """
        Build DB setup based on DB type.

        If SQLite development mode requested, build dual DB setup (given type + )
        """
        setup_class = DBSetupClass.from_db_type(settings.db_type)
        env_vars = self._build_db_env_vars(settings.db_type)
        ret = setup_class(path, env_vars, settings, core)
        return ret

    def _build_db_env_vars(self, db_type: DBType) -> DBEnvVars:
        """
        Build DB env vars for given type of DB.

        In case of SQLite, host = directory of .db file, name = filename; otherwise host and name of database
        """
        db_env_vars_class = DBEnvVarsClass.from_db_type(db_type)

        host_var_name = "MONGO_HOST" if db_type == DBType.mongo else "DB_HOST"
        host_var_value = "db" if db_type == DBType.sqlite else "localhost"
        host_var = EnvVar(name=host_var_name, value=host_var_value)

        db_env_kwargs = {}
        if db_type.value in DBType.sql():
            db_env_kwargs["db_type"] = EnvVar(name="DB_TYPE", value=db_type.value)
            db_env_kwargs["name"] = EnvVar(
                name="DB_NAME",
                value="database",
                service_name=DatabaseEnvVar.from_db_type(db_type),
            )

        if db_type in DBType.service():
            port_var_name_prefix = "MONGO" if db_type == DBType.mongo else "DB"
            db_env_kwargs["port"] = EnvVar(
                name=f"{port_var_name_prefix}_PORT", value=DBPort.from_db_type(db_type)
            )

            auth_name_prefix = "MONGO_INITDB_ROOT" if db_type == DBType.mongo else "DB"
            db_env_kwargs["user"] = EnvVar(
                name=f"{auth_name_prefix}_USER",
                value="changeme",
                service_name=DatabasePrefix.with_var(db_type, "USER"),
            )
            pwd_var = EnvVar(
                name=f"{auth_name_prefix}_PASSWORD",
                value="changeme",
                service_name=DatabasePrefix.with_var(db_type, "PASSWORD"),
            )
            db_env_kwargs["password"] = pwd_var
            if db_type == DBType.mysql:
                db_env_kwargs["root_password"] = EnvVar(
                    name="MYSQL_ROOT_PASSWORD", value=pwd_var.value
                )

        ret = db_env_vars_class(host=host_var, **db_env_kwargs)

        ret.display(header=f"Env vars for {db_type}", debug=True)
        return ret
