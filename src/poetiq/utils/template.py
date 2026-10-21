import enum
from pathlib import Path

from poetiq.logger import logg
from poetiq.enums import ActionType
from poetiq.utils.path import copy_file


class TemplateLocation(str, enum.Enum):
    common_ass = "common_ass"
    setup_ass = "setup_ass"
    poetiq_src = "poetiq_src"
    poetiq_build = "poetiq_build"


class TemplateManager:
    """
    Template manager.

    Util to get paths to poetiq templates and copy templates.

    path: path of the setup
    """

    def __init__(self, setup_type: ActionType, path: Path) -> None:
        self.path = path
        self._setup_type = setup_type

        # FIXME: changes if source file folder depth does
        # TODO: try to use resources - Path() does not convert MultiplexedPath
        # self._path_to_src = Path(resources.files(__package__).__str__()).parent

        # resolves to src/poetiq during testing, site-packages/poetiq during build;
        # in either case contains poetiq's own source files and assets
        self._path_to_root = Path(__file__).resolve().parent.parent
        self._path_to_ass = self._path_to_root / "assets"

        self._template_path_map: dict[TemplateLocation, Path] = {
            TemplateLocation.common_ass: self._path_to_ass,
            TemplateLocation.setup_ass: self._path_to_ass / self._setup_type,
            TemplateLocation.poetiq_src: self._path_to_root,
            TemplateLocation.poetiq_build: self._path_to_root / "_build_assets",
        }

    def copy(
        self,
        template_filename: str,
        package_path: Path | None = None,
        package_filename: str | None = None,
        template_subdir: Path | str | None = None,
        template_location: TemplateLocation = TemplateLocation.setup_ass,
    ) -> Path:
        """
        Copy template into package source code.

        template_filename (str): name of template to copy contained under templates of this package
        TODO: path_in_package subdir same as template for consistency
        path_in_package (Path | None): path where to copy in package; default = root path
        package_filename (str | None): filename of template in package; default = same as original template
        template_subdir (Path): subdirectory of template in main asset path; default = no subdirectory
        template_location (TemplateLocation): location of template:
            common: independent of setup type, is under global common assets
            setup: setup specific, is under assets subfolder corresponding to setup type
            poetiq_build: poetiq build assets, ones not under src/poetiq that are copied during build to _build_assets
            poetiq_src: poetiq's own source files

        Returns path to file in package.
        """
        filename_in_package = package_filename or template_filename
        path_in_package = package_path or self.path
        path_to_package_file = path_in_package / filename_in_package

        path_to_template = self.get_filepath(
            template_filename,
            template_location=template_location,
            subdir=template_subdir,
        )

        copy_file(path_to_template, path_to_package_file)

        return path_to_package_file

    def get_filepath(
        self,
        filename: str,
        template_location: TemplateLocation = TemplateLocation.setup_ass,
        subdir: Path | str | None = None,
    ) -> Path:
        """
        Get full path to template in poetiq.

        filename (str): template filename with extension
        template_type: type of template; default setup specific (most typical)
        subdir (Path): subdirectory in main template directory; default = no subdirectory
        """
        template_dir = self._get_templates_dir(template_location)
        if subdir is not None:
            template_dir = template_dir / subdir
        ret = template_dir / filename
        return ret

    def _get_templates_dir(self, template_type: TemplateLocation) -> Path:
        """
        Get path to templates directory based on given template type.
        """
        ret = self._template_path_map[template_type]
        return ret
