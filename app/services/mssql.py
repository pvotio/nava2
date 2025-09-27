from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

import pyodbc

from ..core.config import settings

logger = logging.getLogger(__name__)


class MSSQLClient:
    def __init__(self, dsn: str | None = None, autocommit: bool = False, timeout: int = 30):
        self.dsn = dsn or settings.MSSQL_DSN
        self.autocommit = autocommit
        self.timeout = timeout
        self.conn: pyodbc.Connection | None = None

    def connect(self):
        if not self.dsn:
            raise RuntimeError("MSSQL_DSN is not configured.")
        logger.debug("Connecting to MSSQL via pyodbc")
        self.conn = pyodbc.connect(self.dsn, autocommit=self.autocommit, timeout=self.timeout)

    def close(self):
        if self.conn:
            try:
                self.conn.close()
            finally:
                self.conn = None

    def __enter__(self) -> MSSQLClient:
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.conn and not self.autocommit:
            if exc:
                self.conn.rollback()
            else:
                self.conn.commit()
        self.close()

    def fetch_all(self, sql: str, params: Iterable[Any] | None = None) -> list[dict]:
        if not self.conn:
            self.connect()
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        cols = [c[0] for c in cur.description] if cur.description else []
        return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]

    def fetch_one(self, sql: str, params: Iterable[Any] | None = None) -> dict | None:
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> int:
        if not self.conn:
            self.connect()
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        return cur.rowcount
