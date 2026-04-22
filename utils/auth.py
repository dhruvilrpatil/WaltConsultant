"""Authentication and session handling for WaltConsultant."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import bcrypt

from database.connection import DatabaseManager, get_db_manager
from utils.constants import ROLE_PERMISSIONS


@dataclass
class AppSession:
    user_id: int | None = None
    username: str = ""
    full_name: str = ""
    role: str = "viewer"
    login_time: str | None = None

    def is_authenticated(self) -> bool:
        return self.user_id is not None

    def clear(self) -> None:
        self.user_id = None
        self.username = ""
        self.full_name = ""
        self.role = "viewer"
        self.login_time = None


class AuthService:
    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db = db_manager or get_db_manager()
        self.session = AppSession()

    @staticmethod
    def hash_password(plain_text_password: str) -> str:
        return bcrypt.hashpw(plain_text_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

    @staticmethod
    def verify_password(plain_text_password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(plain_text_password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False

    def login(self, username_or_email: str, password: str) -> dict[str, Any] | None:
        query = """
            SELECT id, username, full_name, role, password_hash, is_active
            FROM users
            WHERE username = ? OR email = ?
            LIMIT 1
        """
        user = self.db.fetchone(query, (username_or_email.strip(), username_or_email.strip()))
        if not user:
            return None

        if int(user["is_active"]) != 1:
            return None

        if not self.verify_password(password, user["password_hash"]):
            return None

        now = datetime.utcnow().isoformat(timespec="seconds")
        self.db.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user["id"]))

        self.session.user_id = int(user["id"])
        self.session.username = str(user["username"])
        self.session.full_name = str(user["full_name"])
        self.session.role = str(user["role"])
        self.session.login_time = now

        return {
            "id": int(user["id"]),
            "username": str(user["username"]),
            "full_name": str(user["full_name"]),
            "role": str(user["role"]),
            "login_time": now,
        }

    def logout(self) -> None:
        self.session.clear()

    def has_permission(self, module: str, action: str) -> bool:
        role = self.session.role
        allowed_actions = ROLE_PERMISSIONS.get(role, {}).get(module, [])
        return action in allowed_actions

    def register_user(self, payload: dict[str, Any]) -> int:
        with self.db.transaction() as connection:
            row = connection.execute("SELECT id FROM users WHERE username = ? OR email = ?", (payload["username"], payload["email"])).fetchone()
            if row:
                raise ValueError("Username or email already exists.")

            password_hash = self.hash_password(payload["password"])
            cursor = connection.execute(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    username,
                    password_hash,
                    role,
                    phone,
                    address,
                    city,
                    state,
                    pincode,
                    country,
                    date_of_birth,
                    gender,
                    national_id,
                    employment_status,
                    organization,
                    is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["full_name"],
                    payload["email"],
                    payload["username"],
                    password_hash,
                    payload.get("role", "officer"),
                    payload.get("phone"),
                    payload.get("address"),
                    payload.get("city"),
                    payload.get("state"),
                    payload.get("pincode"),
                    payload.get("country", "India"),
                    payload.get("date_of_birth"),
                    payload.get("gender"),
                    payload.get("national_id_number"),
                    payload.get("employment_status"),
                    payload.get("organization"),
                    1,
                ),
            )
            return int(cursor.lastrowid)


AUTH_SERVICE = AuthService()
