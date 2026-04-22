"""SQLite connection management for WaltConsultant."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from utils.constants import DB_FILE_NAME


_SQLITE_CONVERTERS_REGISTERED = False


def _safe_timestamp_converter(value: bytes) -> datetime | str:
    """Accept both datetime and date-only text stored in TIMESTAMP columns."""
    text = value.decode("utf-8", errors="ignore").strip()
    if not text:
        return ""

    try:
        return datetime.fromisoformat(text.replace(" ", "T"))
    except ValueError:
        pass

    try:
        parsed_date = date.fromisoformat(text)
        return datetime.combine(parsed_date, time.min)
    except ValueError:
        return text


def _register_sqlite_converters() -> None:
    global _SQLITE_CONVERTERS_REGISTERED
    if _SQLITE_CONVERTERS_REGISTERED:
        return

    sqlite3.register_converter("timestamp", _safe_timestamp_converter)
    sqlite3.register_converter("TIMESTAMP", _safe_timestamp_converter)
    _SQLITE_CONVERTERS_REGISTERED = True


class DatabaseManager:
    """Centralized SQLite manager with safe defaults for desktop usage."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        _register_sqlite_converters()
        connection = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        connection.execute("PRAGMA journal_mode = WAL;")
        connection.execute("PRAGMA synchronous = NORMAL;")
        connection.execute("PRAGMA busy_timeout = 5000;")
        return connection

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.get_connection() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE;")
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def execute(self, query: str, params: Sequence[Any] | None = None) -> int:
        with self.transaction() as connection:
            cursor = connection.execute(query, params or ())
            return cursor.lastrowid

    def executemany(self, query: str, param_rows: Iterable[Sequence[Any]]) -> None:
        with self.transaction() as connection:
            connection.executemany(query, param_rows)

    def fetchone(self, query: str, params: Sequence[Any] | None = None) -> sqlite3.Row | None:
        with self.get_connection() as connection:
            cursor = connection.execute(query, params or ())
            return cursor.fetchone()

    def fetchall(self, query: str, params: Sequence[Any] | None = None) -> list[sqlite3.Row]:
        with self.get_connection() as connection:
            cursor = connection.execute(query, params or ())
            return cursor.fetchall()


def get_default_db_path() -> Path:
    return Path(__file__).resolve().parents[1] / DB_FILE_NAME


_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(get_default_db_path())
    return _db_manager
