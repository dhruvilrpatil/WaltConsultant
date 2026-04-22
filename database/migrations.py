"""Schema migration runner for WaltConsultant."""

from __future__ import annotations

from sqlite3 import Connection

from database.connection import DatabaseManager, get_db_manager
from database.schema import create_schema, seed_initial_data

CURRENT_SCHEMA_VERSION = 1


def _ensure_version_table(connection: Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _get_current_version(connection: Connection) -> int:
    row = connection.execute("SELECT MAX(version) AS version FROM schema_version").fetchone()
    if not row or row["version"] is None:
        return 0
    return int(row["version"])


def _apply_v1(connection: Connection) -> None:
    create_schema(connection)
    seed_initial_data(connection)


def run_migrations(db_manager: DatabaseManager | None = None) -> int:
    manager = db_manager or get_db_manager()

    with manager.transaction() as connection:
        _ensure_version_table(connection)
        current = _get_current_version(connection)

        if current < 1:
            _apply_v1(connection)
            connection.execute("INSERT INTO schema_version (version) VALUES (?)", (1,))
            current = 1

    return current
