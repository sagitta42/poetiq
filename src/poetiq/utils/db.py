from typing import Any, Optional, TypeVar

from pydantic import BaseModel, Field


class EnvVar(BaseModel):
    """
    Environment variable in .env template or docker-compose.yml
    """

    name: str = Field(description="Variable name")
    value: Any = Field(description="Variable value")
    service_name: Optional[str] = Field(
        default=None,
        description="Variable name in service docker-compose environment; defaults to name",
        exclude=True,
    )

    @property
    def service_env_name(self) -> str:
        return self.service_name or self.name

    @property
    def dollar(self) -> str:
        """
        Get ${var} string.
        """
        ret = f"${{{self.name}}}"
        return ret


class DBEnvVars(BaseModel):
    """
    Database environment variables
    """

    model_config = ConfigDict(extra="forbid")
    host: EnvVar

    @property
    def set_vars(self) -> list[EnvVar]:
        """
        Non null variables
        """
        all_fields = self.__dict__.values()
        ret = [var for var in all_fields if var is not None]
        return ret


class SqlDBEnvVars(DBEnvVars):
    db_type: EnvVar
    name: EnvVar


class HostedDBEnvVars(DBEnvVars):
    port: EnvVar | None
    user: EnvVar
    password: EnvVar


class HostedSqlDBEnvVars(SqlDBEnvVars, HostedDBEnvVars):
    pass


class MySqlDBEnvVars(HostedSqlDBEnvVars):
    root_password: EnvVar


T_DBEnvVars = TypeVar("T_DBEnvVars", bound=DBEnvVars)
T_SqlDBEnvVars = TypeVar("T_SqlDBEnvVars", bound=SqlDBEnvVars)
T_ServiceDBEnvVars = TypeVar("T_ServiceDBEnvVars", bound=HostedDBEnvVars)
