import enum
from pathlib import Path
from typing import Any

import yaml

from poetiq.enums import DBType
from poetiq.utils.db import EnvVar


class DockerImage(enum.StrEnum):
    psql = "postgres:16-alpine"
    mongo = "mongo:8"
    mysql = "mysql:latest"

    @classmethod
    def from_db_type(cls, db_type: DBType) -> str:
        return cls[db_type.name].value


# TODO: use
class DockerHealthCheck(enum.StrEnum):
    psql = '[ "CMD-SHELL", "pg_isready", "-d", "db_prod" ]'
    mongo = "mongosh --eval \"db.adminCommand('ping')\" --quiet"

    @classmethod
    def from_db_type(cls, db_type: DBType) -> str:
        return cls[db_type.name].value


# TODO: volume


class DockerComposeHandler:
    """
    Handler for managing docker-compose.yml
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.docker_compose = self.path / "docker-compose.yml"

    def add_volume(self, vol: str):
        """
        Add given volume to list of volumes.
        """
        yml_info = self._read(with_section="volumes")
        volumes = yml_info["volumes"]

        if vol not in volumes:
            volumes[vol] = None

        self._write(yml_info)

    def _read(self, with_section: str | None = None) -> dict[str, Any]:
        """
        Get docker-compose from given path to .yml.

        If does not exist, set up empty "services" in dict.
        """

        yml_info = {}
        if self.docker_compose.exists():
            with open(self.docker_compose) as f:
                yml_info = yaml.safe_load(f)

        if with_section is not None and with_section not in yml_info:
            yml_info[with_section] = {}

        return yml_info

    def _write(self, info: dict[str, Any]):
        # FIXME: improve duplication
        with open(self.docker_compose, "w") as f:
            yaml.dump(info, f)


class DockerComposeServiceHandler(DockerComposeHandler):
    def __init__(self, path: Path, service_name: str) -> None:
        super().__init__(path)

        self._name = service_name

    def rename(self, new_name: str):
        """
        Rename service.
        """
        yml_info = super()._read()

        services = yml_info["services"]
        services[new_name] = services.pop(self._name)
        super()._write(yml_info)

        self._name = new_name

    def get_volumes(self) -> list[str]:
        """
        Get volumes of given service, if specified
        """
        service = self._read(with_section="volumes", init=list)
        ret = [volume_info.split(":")[0] for volume_info in service["volumes"]]
        return ret

    def set_image(self, db_type: DBType):
        """
        Set service image for given DB type.
        """
        self._set_item("image", DockerImage.from_db_type(db_type))

    def set_container_name(self, name: str):
        """
        Set container name of given service.
        """
        self._set_item("container_name", name)

    def set_port(self, port: EnvVar):
        """
        Set service port.

        Sets given port and does not replace existing ports
        """
        service_info = self._read(with_section="ports", init=list)
        ports = service_info["ports"]

        port_str = f"{port.dollar}:{port.value}"
        if len(ports) > 0:
            ports[0] = port_str
        else:
            ports.append(port_str)

        self._set_item("ports", ports)

    def set_dockerfile(self, name: str):
        """
        Set dockerfile with given name in build
        """
        build_info = {"context": ".", "dockerfile": name}
        self._set_item("build", build_info)

    def set_env_var(self, var: str, value: str):
        """
        Set environment variable value in service.

        Sets only given variable and does not replace existing environment.
        """
        service_info = self._read(with_section="environment")
        env = service_info["environment"]

        env[var] = value
        self._set_item("environment", env)

    def update_env_vars(self, env_vars: list[EnvVar], user_service_var_names: bool):
        """
        Set/update environment variables db service.

        user_service_var_names: use service variable names (e.g. POSTGRES_PASSWORD) in environment
            instead of same as .env names

        Set environment variable to be picked up from .env.template
            with the same name i.e. ${VAR} format.
        """
        for env_var in env_vars:
            var_name = (
                env_var.service_env_name if user_service_var_names else env_var.name
            )
            self.set_env_var(var_name, env_var.dollar)

    def set_from_template(self, path_to_template: Path):
        """
        Set service info based on one in given template.

        Create file if does not exist yet.
        Will replace whatever contents prior if existed prior.
        """
        service_info = self._read()

        with open(path_to_template) as f:
            yml_template = yaml.safe_load(f)

        services_template = yml_template["services"]

        if self._name not in services_template:
            raise ValueError(
                f"Service {self._name} not present in template {path_to_template}!"
            )

        service_info = services_template[self._name]

        self._write(service_info)

    def _set_item(self, name: str, value: Any):
        """
        Set item to value in service.

        Will replace previous value.
        """
        service_info = self._read()
        service_info[name] = value
        self._write(service_info)

    def _read(
        self, with_section: str | None = None, init: type = dict
    ) -> dict[str, Any]:
        """
        Get service info from docker-compose.

        If service not present, will add empty info.
        """
        yml_info = super()._read(with_section="services")
        services = yml_info["services"]

        if self._name not in services:
            services[self._name] = {}

        ret = services[self._name]

        if with_section is not None and with_section not in ret:
            ret[with_section] = init()

        return ret

    def _write(self, info: dict[str, Any]):
        """
        Set docker compose service with given dict.

        Will replace whatever info was there prior if any.
        """
        yml_info = super()._read(with_section="services")

        yml_info["services"][self._name] = info
        # TODO: store docker compose in member, update, write at the end
        super()._write(yml_info)
