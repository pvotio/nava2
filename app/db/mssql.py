from contextlib import contextmanager

import pyodbc

from ..core.config import settings


def _connect():
    # Uses raw ODBC connection string from env: MSSQL_DSN
    return pyodbc.connect(settings.MSSQL_DSN)


@contextmanager
def mssql_cursor():
    cn = _connect()
    try:
        yield cn.cursor()
    finally:
        cn.close()
