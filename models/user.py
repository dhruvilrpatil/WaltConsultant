"""User model operations for WaltConsultant."""

from __future__ import annotations

from typing import Any

from database.connection import DatabaseManager, get_db_manager
from utils.audit import AUDIT_LOGGER
from utils.auth import AuthService, AUTH_SERVICE


class UserModel:
    def __init__(self, db_manager: DatabaseManager | None = None, auth_service: AuthService | None = None) -> None:
        self.db = db_manager or get_db_manager()
        self.auth = auth_service or AUTH_SERVICE

    def list_users(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT id, full_name, email, username, role, phone, city, state, created_at, last_login, is_active
            FROM users
            ORDER BY created_at DESC
            """
        )
        return [dict(row) for row in rows]

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        row = self.db.fetchone(
            """
            SELECT id, full_name, email, username, role, phone, address, city, state, pincode, country,
                   date_of_birth, gender, national_id, employment_status, organization, created_at, last_login, is_active
            FROM users WHERE id = ?
            """,
            (user_id,),
        )
        return dict(row) if row else None

    def create_officer(self, payload: dict[str, Any], actor_user_id: int | None = None) -> int:
        payload = dict(payload)
        payload.setdefault("role", "officer")
        user_id = self.auth.register_user(payload)
        AUDIT_LOGGER.log_action(actor_user_id, "INSERT", "users", user_id, None, payload)
        return user_id

    def update_role(self, user_id: int, role: str, actor_user_id: int | None = None) -> None:
        old_user = self.get_user_by_id(user_id)
        if not old_user:
            raise ValueError("User not found.")

        self.db.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        AUDIT_LOGGER.log_action(actor_user_id, "UPDATE", "users", user_id, old_user, {"role": role})

    def deactivate_user(self, user_id: int, actor_user_id: int | None = None) -> None:
        old_user = self.get_user_by_id(user_id)
        if not old_user:
            raise ValueError("User not found.")

        self.db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        AUDIT_LOGGER.log_action(actor_user_id, "UPDATE", "users", user_id, old_user, {"is_active": 0})


USER_MODEL = UserModel()
