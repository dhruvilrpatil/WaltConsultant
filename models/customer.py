"""Customer model operations for WaltConsultant."""

from __future__ import annotations

from typing import Any

from database.connection import DatabaseManager, get_db_manager
from utils.audit import AUDIT_LOGGER
from utils.formatters import now_iso
from utils.validators import validate_customer_fields


class CustomerModel:
    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db = db_manager or get_db_manager()

    def _next_customer_id(self, connection) -> str:
        row = connection.execute(
            """
            SELECT COALESCE(MAX(CAST(SUBSTR(customer_id, 11) AS INTEGER)), 0) AS seq
            FROM customers
            WHERE customer_id LIKE 'WALT-CUST-%'
            """
        ).fetchone()
        seq = (row[0] if row else 0) + 1
        return f"WALT-CUST-{seq:05d}"

    def list_customers(self, search: str = "") -> list[dict[str, Any]]:
        search = f"%{search.strip()}%"
        rows = self.db.fetchall(
            """
            SELECT c.id, c.customer_id, c.full_name, c.email, c.phone, c.city, c.credit_score, c.is_active,
                   COUNT(l.id) AS active_loans
            FROM customers c
            LEFT JOIN loans l ON l.customer_id = c.id AND l.status IN ('active', 'disbursed', 'approved') AND l.is_deleted = 0
            WHERE (c.full_name LIKE ? OR c.customer_id LIKE ? OR c.phone LIKE ?)
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """,
            (search, search, search),
        )
        return [dict(row) for row in rows]

    def get_customer(self, customer_id: int) -> dict[str, Any] | None:
        row = self.db.fetchone("SELECT * FROM customers WHERE id = ?", (customer_id,))
        return dict(row) if row else None

    def create_customer(self, payload: dict[str, Any], actor_user_id: int | None) -> int:
        errors = validate_customer_fields(payload)
        if errors:
            raise ValueError("; ".join(errors.values()))

        with self.db.transaction() as connection:
            duplicate = connection.execute(
                "SELECT id FROM customers WHERE email = ? OR phone = ? LIMIT 1",
                (payload["email"], payload["phone"]),
            ).fetchone()
            if duplicate:
                raise ValueError("Customer with same email or phone already exists.")

            public_id = self._next_customer_id(connection)
            cursor = connection.execute(
                """
                INSERT INTO customers (
                    customer_id, full_name, email, phone, alternate_phone, date_of_birth, gender,
                    address_line1, address_line2, city, state, pincode, country,
                    national_id_type, national_id_number, employment_status, employer_name,
                    monthly_income, credit_score, bank_name, bank_account_number, bank_ifsc,
                    nominee_name, nominee_relation, nominee_phone, notes, created_by, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    public_id,
                    payload["full_name"],
                    payload["email"],
                    payload["phone"],
                    payload.get("alternate_phone"),
                    payload.get("date_of_birth"),
                    payload.get("gender"),
                    payload.get("address_line1"),
                    payload.get("address_line2"),
                    payload.get("city"),
                    payload.get("state"),
                    payload.get("pincode"),
                    payload.get("country", "India"),
                    payload.get("national_id_type"),
                    payload.get("national_id_number"),
                    payload.get("employment_status"),
                    payload.get("employer_name"),
                    payload.get("monthly_income"),
                    payload.get("credit_score"),
                    payload.get("bank_name"),
                    payload.get("bank_account_number"),
                    payload.get("bank_ifsc"),
                    payload.get("nominee_name"),
                    payload.get("nominee_relation"),
                    payload.get("nominee_phone"),
                    payload.get("notes"),
                    actor_user_id,
                    now_iso(),
                    1,
                ),
            )
            customer_row_id = int(cursor.lastrowid)

        AUDIT_LOGGER.log_action(actor_user_id, "INSERT", "customers", customer_row_id, None, payload)
        return customer_row_id

    def update_customer(self, customer_id: int, payload: dict[str, Any], actor_user_id: int | None) -> None:
        old_data = self.get_customer(customer_id)
        if not old_data:
            raise ValueError("Customer not found.")

        self.db.execute(
            """
            UPDATE customers
            SET full_name = ?, email = ?, phone = ?, city = ?, state = ?, pincode = ?,
                updated_at = ?, notes = ?, is_active = ?
            WHERE id = ?
            """,
            (
                payload.get("full_name", old_data["full_name"]),
                payload.get("email", old_data["email"]),
                payload.get("phone", old_data["phone"]),
                payload.get("city", old_data.get("city")),
                payload.get("state", old_data.get("state")),
                payload.get("pincode", old_data.get("pincode")),
                now_iso(),
                payload.get("notes", old_data.get("notes")),
                payload.get("is_active", old_data.get("is_active", 1)),
                customer_id,
            ),
        )
        AUDIT_LOGGER.log_action(actor_user_id, "UPDATE", "customers", customer_id, old_data, payload)

    def deactivate_customer(self, customer_id: int, actor_user_id: int | None) -> None:
        old_data = self.get_customer(customer_id)
        if not old_data:
            raise ValueError("Customer not found.")

        self.db.execute("UPDATE customers SET is_active = 0, updated_at = ? WHERE id = ?", (now_iso(), customer_id))
        AUDIT_LOGGER.log_action(actor_user_id, "DELETE", "customers", customer_id, old_data, {"is_active": 0})


CUSTOMER_MODEL = CustomerModel()
