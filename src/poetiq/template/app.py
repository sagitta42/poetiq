import os
from pathlib import Path

from poetiq.setup.db.base.base import BaseDBSetup
from poetiq.setup.db.base.docker import DockerDBSetup
from poetiq.setup.db.factory import DBSetupFactory
from poetiq.setup.db.mongo import MongoDBSetup
from poetiq.setup.env_settings import EnvSettingsSetup
from poetiq.enums import ActionType, DBType
from poetiq.settings.setup import DBSettings
from poetiq.settings.template import AppTemplateSettings
from poetiq.template.base import BaseTemplate
from poetiq.utils.docker import DockerComposeHandler, DockerComposeServiceHandler


class AppTemplate(BaseTemplate[AppTemplateSettings]):
    def __init__(self, path: Path | None, settings: AppTemplateSettings) -> None:
        super().__init__(path, settings)

        self._env_settings_setup = EnvSettingsSetup(
            self.path, template_setup=ActionType.db, core=False
        )
        db_setup_factory = DBSetupFactory()
        self._db: BaseDBSetup | None = (
            None
            if settings.db_type == DBType.none
            else db_setup_factory.build(
                self.path,
                DBSettings(db_type=settings.db_type, dev_sqlite=settings.dev_sqlite),
                core=False,
            )
        )

        self._mongodb: MongoDBSetup | None = (
            db_setup_factory.build(
                self.path, DBSettings(db_type=DBType.mongo), core=False
            )
            if self._settings.mongodb
            else None
        )

        self._service = DockerComposeServiceHandler(self.path, "app")
        self._docker = DockerComposeHandler(self.path)

    def _poetry_init(self):
        """
        Initialize package with poetry.

        Basic setup with only pyproject.toml.
        Disable package mode.
        """
        os.makedirs(self.path, exist_ok=True)

        super()._poetry_init()

    def setup(self) -> None:
        """
        App template setup.

        In addition to standard template setup:
            - docker compose file
            - DB if requested

        Note: set up docker-compose file last to assign volumes.
        TODO: set up other things like port and host based on existing docker file
            rather than in-code (?)
        """
        super().setup()

        if self._db is not None:
            self._db.setup()

        if self._mongodb is not None:
            self._mongodb.setup()

        self.setup_docker_compose()

    def setup_dependencies(self) -> None:
        """
        Set up dependencies.
        """
        super().setup_dependencies()

        self._poetry_add("fastapi")
        self._poetry_add("uvicorn")

    def setup_source_files(self):
        """
        Set up source files.

        Set up subfolder structure.
        Set up settings and app info.
        Set up dummy source files for core logic, services, schemas, and routers.
        Set up main uvicorn launchable script.
        """
        self._setup_subfolders()

        self._templates.copy("app_info.py")

        package_filename = "dummy.py"

        core_templates = "core"
        path_to_core = self.path / "core"
        self._templates.copy(
            "core.py",
            package_path=path_to_core,
            package_filename=package_filename,
            template_subdir=core_templates,
        )
        if self._db is not None:
            self._templates.copy(
                "db.py", package_path=path_to_core, template_subdir=core_templates
            )
            self._templates.copy(
                "model.py",
                package_path=path_to_core / "models",
                package_filename="example.py",
                template_subdir=core_templates,
            )

        # TODO: #44 part of mongod setup to enable standalone poetiq setup db --db-type mongodb
        # (source files in given subdir)
        if self._mongodb is not None:
            for mongo_template in ["db_mongo.py", "mongo_config.py"]:
                self._templates.copy(
                    mongo_template,
                    package_path=path_to_core,
                    template_subdir=core_templates,
                )

            self._templates.copy(
                "mongo_document.py",
                package_path=path_to_core / "models",
                template_subdir=core_templates,
            )

        path_to_app = self.path / "app"
        self._templates.copy(
            "service.py",
            package_path=path_to_app / "services",
            package_filename=package_filename,
        )
        self._templates.copy(
            "schemas.py",
            package_path=path_to_app / "schemas",
            package_filename=package_filename,
        )

        route_file = "route.py" if self._db is None else "route_db.py"
        path_to_api = path_to_app / "api"
        self._templates.copy(
            route_file,
            package_path=path_to_api / "routes",
            package_filename=package_filename,
        )
        self._templates.copy("router.py", package_path=path_to_api)

        self._templates.copy("main.py")

    def setup_docker_compose(self):
        """
        Set up docker compose.

        Copy template and set container name.
        Set up dockerfile.
        Set up DB env variables in app service.
        Set app host env variable to db service name.
        Set up volumes based on info in each service.
        """
        path_to_template = self._templates.get_filepath("docker-compose.yml")
        self._service.set_from_template(path_to_template)
        self._service.set_container_name(f"{self.name}_app")

        self._templates.copy("dockerfile")
        self._service.set_dockerfile("dockerfile")

        docker_dbs: list[DockerDBSetup] = []
        if self._db is not None and isinstance(self._db.main, DockerDBSetup):
            docker_dbs.append(self._db.main)
        if self._mongodb is not None:
            docker_dbs.append(self._mongodb)

        for db in docker_dbs:
            self._service.update_env_vars(
                db.docker_env_vars.set_vars, user_service_var_names=False
            )

            db_host = db.docker_env_vars.host.model_copy()
            self._service.set_env_var(db_host.name, db.service_name)

        all_services = [self._service] + [db._service for db in docker_dbs]
        for service in all_services:
            for vol in service.get_volumes():
                self._docker.add_volume(vol)

    def _setup_subfolders(self):
        """
        Set up subfolders.

        app: app code (api, schemas, routers, serviecs)
        core: core logic/engine code
        """

        for subfolder in ["app", "core"]:
            os.makedirs(self.path / subfolder, exist_ok=True)

        if any(db is not None for db in [self._db, self._mongodb]):
            os.makedirs(self.path / "core" / "models", exist_ok=True)

        for app_subfolder in ["api", "schemas", "services"]:
            os.makedirs(self.path / "app" / app_subfolder, exist_ok=True)

        os.makedirs(self.path / "app" / "api" / "routes", exist_ok=True)
