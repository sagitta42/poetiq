from contextlib import contextmanager
from typing import Any

import pandas as pd
from sqlalchemy import Connection, Engine, create_engine, inspect, text

from settings import DBSettings, get_url


class DB:
    def __init__(self, settings: DBSettings) -> None:
        self._settings = settings

    def read_table(
        self, table: str, columns: list[str] | None, date_columns: list[str] = []
    ) -> pd.DataFrame:
        """
        Read table from DB.

        date_columns (list[str]): list of column names to parse as dates

        If no columns provided, read all columns.
        """
        with self._get_engine() as engine:
            ret = pd.read_sql_table(
                table, columns=columns, parse_dates=date_columns, con=engine
            )
        return ret

    def describe_table(self, table: str) -> pd.DataFrame:
        with self._get_engine() as engine:
            ret = pd.read_sql_query(f"describe {table}", con=engine)
        return ret

    def query(self, query: str) -> list[dict[str, Any]]:
        """
        Apply given query.

        Return rows in dict form.
        """
        with self._get_engine() as engine:
            with engine.connect() as conn:
                rows = self._query(query, conn)
                return rows

        return rows

    def get_list_of_tables(self) -> list[str]:
        """
        List of tablenames.
        """
        with self._get_engine() as engine:
            inspector = inspect(engine)
            ret = inspector.get_table_names()
        return ret

    def _query(self, query: str, conn: Connection) -> list[dict[str, Any]]:
        """
        Get result of given query from connection.
        """
        result = conn.execute(text(query))
        rows = [dict(row._mapping) for row in result]
        return rows

    @contextmanager
    def _get_engine(self):
        """
        Create connection engine.
        """
        engine = self._create_engine()

        try:
            yield engine
        finally:
            engine.dispose()

    def _create_engine(self) -> Engine:
        url = get_url(self._settings)
        engine = create_engine(url)
        return engine
