from pathlib import Path

from poetiq.setup.db.base.single import SingleDBSetup
from poetiq.logger import logg
from poetiq.settings.setup import DBSettings
from poetiq.utils.db import HostedDBEnvVars, T_ServiceDBEnvVars
from poetiq.utils.docker import DockerComposeServiceHandler


class DockerDBSetup(SingleDBSetup[T_ServiceDBEnvVars]):
    """
    DB setup that includes setting up docker-compose.

    service_name: Service name in docker-compose

    E.g. MogoDB or psql
    """

    def __init__(
        self, path: Path, env_vars: T_ServiceDBEnvVars, settings: DBSettings, core: bool
    ) -> None:
        super().__init__(path, env_vars, settings, core)

        self.service_name: str = f"db_{self.db_type}"
        self._service = DockerComposeServiceHandler(self.path, self.service_name)

    @property
    def docker_env_vars(self) -> HostedDBEnvVars:
        """
        Docker env variables.

        .env template DB variables except port
        """
        ret = self._env_vars.model_copy()
        ret.port = None
        return ret

    def setup(self):
        super().setup()

        self.setup_docker_compose()

    def setup_docker_compose(self):
        """
        Set up docker-compose.

        Set up DB service in docker-compose from template.
        Set service and container name.
        Set up image.
        Set up environment variables in service environment.
        Set up port.
        """
        logg.info(f"- setting up {self.db_type} docker-compose.yml")

        path_to_template = self._templates.get_filepath(
            "docker-compose.yml", subdir=self.db_type.value
        )
        self._service.set_from_template(path_to_template)

        self._service.rename(self.service_name)
        self._service.set_container_name(self.service_name)

        self._service.set_image(self.db_type)

        self._service.update_env_vars(
            self.docker_env_vars.set_vars, user_service_var_names=True
        )
        assert self._env_vars.port is not None, "got None for port for docker DB setup"
        self._service.set_port(self._env_vars.port)
