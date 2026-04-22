"""Repayment model operations for WaltConsultant."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from database.connection import DatabaseManager, get_db_manager
from utils.audit import AUDIT_LOGGER
from utils.constants import PAYMENT_MODES
from utils.formatters import now_iso


class RepaymentModel:
    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db = db_manager or get_db_manager()

    def _next_repayment_id(self, connection) -> str:
        row = connection.execute(
            """
            SELECT COALESCE(MAX(CAST(SUBSTR(repayment_id, 10) AS INTEGER)), 0) AS seq
            FROM repayments
            WHERE repayment_id LIKE 'WALT-RPY-%'
            """
        ).fetchone()
        seq = (row[0] if row else 0) + 1
        return f"WALT-RPY-{seq:05d}"

    def list_repayments(self, status: str = "", search: str = "") -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = ["1=1"]

        if status:
            conditions.append("r.status = ?")
            params.append(status)

        if search.strip():
            like = f"%{search.strip()}%"
            conditions.append("(r.repayment_id LIKE ? OR l.loan_number LIKE ? OR c.full_name LIKE ?)")
            params.extend([like, like, like])

        query = f"""
            SELECT r.id, r.repayment_id, l.loan_number, c.full_name AS customer_name,
                   r.installment_number, r.due_date, r.paid_date, r.emi_amount,
                   r.status, r.payment_mode, r.total_paid
            FROM repayments r
            JOIN loans l ON l.id = r.loan_id
            JOIN customers c ON c.id = r.customer_id
            WHERE {' AND '.join(conditions)}
            ORDER BY r.created_at DESC
        """
        rows = self.db.fetchall(query, tuple(params))
        return [dict(row) for row in rows]

    def due_today(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT ls.loan_id, l.loan_number, c.full_name AS customer_name,
                   ls.installment_number, ls.due_date, ls.emi_amount
            FROM loan_schedule ls
            JOIN loans l ON l.id = ls.loan_id
            JOIN customers c ON c.id = l.customer_id
            WHERE ls.status IN ('pending', 'overdue')
              AND ls.due_date = date('now')
              AND l.status IN ('active', 'disbursed', 'approved')
            ORDER BY l.loan_number
            """
        )
        return [dict(row) for row in rows]

    def _next_pending_schedule(self, connection, loan_id: int):
        return connection.execute(
            """
            SELECT ls.*, l.customer_id
            FROM loan_schedule ls
            JOIN loans l ON l.id = ls.loan_id
            WHERE ls.loan_id = ? AND ls.status IN ('pending', 'overdue', 'partial')
            ORDER BY ls.installment_number ASC
            LIMIT 1
            """,
            (loan_id,),
        ).fetchone()

    def record_payment(self, payload: dict[str, Any], actor_user_id: int | None) -> int:
        paid_date = payload.get("paid_date") or date.today().isoformat()
        payment_mode = payload.get("payment_mode", "UPI")
        if payment_mode not in PAYMENT_MODES:
            raise ValueError("Invalid payment mode selected.")

        with self.db.transaction() as connection:
            loan_id = int(payload["loan_id"])
            pending_schedule = self._next_pending_schedule(connection, loan_id)
            if not pending_schedule:
                raise ValueError("No pending installment found for this loan.")

            due = datetime.strptime(pending_schedule["due_date"], "%Y-%m-%d").date()
            paid = datetime.strptime(paid_date, "%Y-%m-%d").date()
            days_late = (paid - due).days
            late_fee = round(max(0, days_late) * 2.0, 2)

            total_paid = float(payload.get("payment_amount") or pending_schedule["emi_amount"])
            repayment_id = self._next_repayment_id(connection)

            cursor = connection.execute(
                """
                INSERT INTO repayments (
                    repayment_id,
                    loan_id,
                    customer_id,
                    installment_number,
                    due_date,
                    paid_date,
                    principal_component,
                    interest_component,
                    emi_amount,
                    late_fee,
                    total_paid,
                    payment_mode,
                    transaction_reference,
                    status,
                    collected_by,
                    remarks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    repayment_id,
                    loan_id,
                    pending_schedule["customer_id"],
                    pending_schedule["installment_number"],
                    pending_schedule["due_date"],
                    paid_date,
                    pending_schedule["principal_component"],
                    pending_schedule["interest_component"],
                    pending_schedule["emi_amount"],
                    late_fee,
                    total_paid,
                    payment_mode,
                    payload.get("transaction_reference"),
                    "paid",
                    actor_user_id,
                    payload.get("remarks"),
                ),
            )
            repayment_row_id = int(cursor.lastrowid)

            connection.execute(
                """
                UPDATE loan_schedule
                SET status = 'paid'
                WHERE loan_id = ? AND installment_number = ?
                """,
                (loan_id, pending_schedule["installment_number"]),
            )

            remaining = connection.execute(
                "SELECT COUNT(*) AS count FROM loan_schedule WHERE loan_id = ? AND status <> 'paid'",
                (loan_id,),
            ).fetchone()[0]

            new_status = "closed" if remaining == 0 else "active"
            connection.execute("UPDATE loans SET status = ?, updated_at = ? WHERE id = ?", (new_status, now_iso(), loan_id))

        AUDIT_LOGGER.log_action(actor_user_id, "INSERT", "repayments", repayment_row_id, None, payload)
        return repayment_row_id

    def update_overdue_statuses(self, actor_user_id: int | None = None) -> int:
        with self.db.transaction() as connection:
            rows = connection.execute(
                """
                SELECT id, loan_id, due_date
                FROM loan_schedule
                WHERE status = 'pending' AND due_date < date('now')
                """
            ).fetchall()

            for row in rows:
                connection.execute("UPDATE loan_schedule SET status = 'overdue' WHERE id = ?", (row["id"],))
                connection.execute(
                    """
                    INSERT INTO notifications (user_id, title, message, type)
                    SELECT created_by,
                           'EMI Overdue',
                           ?,
                           'warning'
                    FROM loans WHERE id = ?
                    """,
                    (f"Loan {row['loan_id']} installment due on {row['due_date']} is overdue.", row["loan_id"]),
                )

            connection.execute(
                """
                UPDATE loans
                SET status = 'defaulted', updated_at = ?
                WHERE id IN (
                    SELECT loan_id
                    FROM loan_schedule
                    WHERE status = 'overdue'
                    GROUP BY loan_id
                    HAVING COUNT(*) >= 3
                )
                """,
                (now_iso(),),
            )

        if rows:
            AUDIT_LOGGER.log_action(actor_user_id, "UPDATE", "loan_schedule", None, None, {"overdue_updated": len(rows)})
        return len(rows)


REPAYMENT_MODEL = RepaymentModel()
