from pydantic import BaseModel

PackageName = str


def get_package_def(package_str: str, split_str: str) -> tuple[PackageName, str]:
    """
    Get package definition splitting dependency string by given split string.

    E.g. package==1.2.3, package @ path
    """
    package, info = [component.strip() for component in package_str.split(split_str)]
    return package, info


def get_package_version(package_str: str) -> tuple[PackageName, str]:
    """
    Extract package version from string.

    Types of formats parsed:
        - package-name==1.2.3 (pip freeze)
        - package-name (==1.2.3)" (pyproject.toml)
        - package-name (>=0.141.1,<0.142.0)"
    """
    if "==" in package_str:
        package, version = get_package_def(package_str, "==")
        package = package.replace("(", "").rstrip()
    elif ">" in package_str or "<" in package_str:
        package, version = get_package_def(package_str, "(")
    else:
        raise NotImplementedError(
            f"Could not parse package info format {package_str}! Checking for ==/</> type formats; unrecognized"
        )

    version = version.replace(")", "")

    return package, version


def get_egg_package(package_str: str) -> tuple[PackageName, str]:
    """
    Extract package name and source from "-e ... egg=package" pip string.

    Example:
    -e git+https://github.com/user/package-name.git@77c73b422d3326d14c1e930239c00a3ce460bc78#egg=package_name
    """
    source, package = package_str.split("#egg=")
    source = source.removeprefix("-e").lstrip()
    package = package.replace("_", "-")
    return package, source


def get_package_source(package_str: str) -> tuple[PackageName, str]:
    """
    Extract package name and source from "package @ source" pip string.

    Remove final "/" if filepath.
    """
    package, path = get_package_def(package_str, " @ ")
    path = path.removesuffix("/")
    return package, path


class Package(BaseModel):
    name: PackageName
    version: str | None
    source: str | None

    @property
    def source_str(self) -> str:
        """
        Create poetry add / pip install string.

        Examples:
            package-name==1.2.3
            package-name>=0.2,<0.3
            git+ssh://
            git+https://
            file://

        Add git+ if source is detected to be path to local .git repo clone or git@
        """

        prepend = ""
        if self.source is None:
            # TODO: validator
            assert self.version is not None, "must have version if source is null"
            ret = (
                f"{self.name}{self.version}"
                if ">" in self.version or "<" in self.version
                else f"{self.name}=={self.version}"
            )
            return ret

        prepend = ""
        if self.source.startswith("git@") or self.source.endswith(".git"):
            prepend = "git+"
            if self.source.startswith("git@"):
                prepend += "ssh://"
            elif not any(self.source.startswith(start) for start in ["https", "ssh"]):
                prepend += "file://"

        ret = prepend + self.source
        return ret

    @classmethod
    def from_package_str(cls, package_str: str) -> "Package":
        """
        Get package info from string.

        Interpret the following formats of package info:
        - source: package-name @ source or package-name @ filepath (preserves file:// prefix)
        - version: package-name == version
        - egg: -e ... egg=package-name
        """
        if package_str.startswith("-e") and "#egg=" in package_str:
            name, source = get_egg_package(package_str)
            version = None
        elif "@" in package_str:
            name, source = get_package_source(package_str)
            version = None
        elif any(mark in package_str for mark in ["==", "<", ">"]):
            name, version = get_package_version(package_str)
            source = None
        else:
            raise NotImplementedError(
                f"Could not parse package info format {package_str}! Checking for @, ==/>/<, -e type formats; unrecognized"
            )
        ret = cls(name=name, version=version, source=source)
        return ret
