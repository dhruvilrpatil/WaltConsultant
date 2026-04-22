"""Audit helpers for WaltConsultant."""

from __future__ import annotations

import json
from typing import Any

from database.connection import DatabaseManager, get_db_manager


class AuditLogger:
    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db = db_manager or get_db_manager()

    def log_action(
        self,
        user_id: int | None,
        action: str,
        module: str,
        record_id: int | None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        ip_address: str = "127.0.0.1",
    ) -> None:
        self.db.execute(
            """
            INSERT INTO audit_log (
                user_id,
                action,
                module,
                record_id,
                old_value,
                new_value,
                ip_address
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                action,
                module,
                record_id,
                json.dumps(old_value or {}, default=str),
                json.dumps(new_value or {}, default=str),
                ip_address,
            ),
        )


AUDIT_LOGGER = AuditLogger()
