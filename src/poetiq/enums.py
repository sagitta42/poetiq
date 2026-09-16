import enum


class ActionType(enum.StrEnum):
    package = "package"
    app = "app"
    db = "db"
    envsettings = "envsettings"
    vscode = "vscode"
    gitignore = "gitignore"
    progressbar = "progressbar"
    logger = "logger"
    install = "install"
    add = "add"
    lock = "lock"

    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class DBType(enum.StrEnum):
    sqlite = "sqlite"
    psql = "psql"
    mysql = "mysql"
    mongo = "mongo"
    none = "none"

    @classmethod
    def all(cls) -> list[str]:
        """
        All DB types.

        None (no DB) is excluded (not a DB type, a flag to set up no DB)
        """
        all_types = [db_type for db_type in cls if not db_type == cls.none]
        ret = cls._values(all_types)
        return ret

    @classmethod
    def sql(cls) -> list[str]:
        """
        SQL based DB types.
        """
        sql_types = [cls.sqlite, cls.psql, cls.mysql]
        ret = cls._values(sql_types)
        return ret

    @classmethod
    def service(cls) -> list["DBType"]:
        """
        Service DBs
        """
        ret = [cls.psql, cls.mysql, cls.mongo]
        return ret

    @classmethod
    def with_none(cls, db_types: list[str]) -> list[str]:
        """
        Include none (no DB) with given types
        """
        ret = db_types + [cls.none.value]
        return ret

    @classmethod
    def _values(cls, db_types: list) -> list[str]:
        """
        Return str values of list of given db types.
        """
        ret = [db.value for db in db_types]
        return ret
