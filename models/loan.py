"""Loan model operations for WaltConsultant."""

from __future__ import annotations

from datetime import date
from typing import Any

from database.connection import DatabaseManager, get_db_manager
from utils.audit import AUDIT_LOGGER
from utils.calculations import calculate_emi_summary, generate_amortization_schedule
from utils.formatters import now_iso
from utils.validators import validate_loan_fields


class LoanModel:
    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db = db_manager or get_db_manager()

    def _next_loan_number(self, connection, on_date: date) -> str:
        prefix = f"WALT-LN-{on_date.strftime('%Y%m%d')}-"
        row = connection.execute(
            """
            SELECT COALESCE(MAX(CAST(SUBSTR(loan_number, -5) AS INTEGER)), 0) AS seq
            FROM loans
            WHERE loan_number LIKE ?
            """,
            (f"{prefix}%",),
        ).fetchone()
        seq = (row[0] if row else 0) + 1
        return f"{prefix}{seq:05d}"

    def list_loans(self, status: str = "", search: str = "") -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = ["l.is_deleted = 0"]

        if status:
            conditions.append("l.status = ?")
            params.append(status)

        if search.strip():
            conditions.append("(l.loan_number LIKE ? OR c.full_name LIKE ?)")
            like = f"%{search.strip()}%"
            params.extend([like, like])

        query = f"""
            SELECT l.id, l.loan_number, c.full_name AS customer_name, lt.name AS loan_type,
                   l.principal_amount, l.interest_rate, l.tenure_months, l.emi_amount,
                   l.disbursement_date, l.status
            FROM loans l
            JOIN customers c ON c.id = l.customer_id
            JOIN loan_types lt ON lt.id = l.loan_type_id
            WHERE {' AND '.join(conditions)}
            ORDER BY l.created_at DESC
        """
        rows = self.db.fetchall(query, tuple(params))
        return [dict(row) for row in rows]

    def get_loan(self, loan_id: int) -> dict[str, Any] | None:
        row = self.db.fetchone(
            """
            SELECT l.*, c.full_name AS customer_name, c.customer_id AS customer_public_id, lt.name AS loan_type_name
            FROM loans l
            JOIN customers c ON c.id = l.customer_id
            JOIN loan_types lt ON lt.id = l.loan_type_id
            WHERE l.id = ?
            """,
            (loan_id,),
        )
        return dict(row) if row else None

    def get_loan_schedule(self, loan_id: int) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT installment_number, due_date, opening_balance, emi_amount,
                   principal_component, interest_component, closing_balance, status
            FROM loan_schedule
            WHERE loan_id = ?
            ORDER BY installment_number ASC
            """,
            (loan_id,),
        )
        return [dict(row) for row in rows]

    def create_loan(self, payload: dict[str, Any], actor_user_id: int | None) -> int:
        errors = validate_loan_fields(payload)
        if errors:
            raise ValueError("; ".join(errors.values()))

        customer_id = int(payload["customer_id"])
        loan_type_id = int(payload["loan_type_id"])
        principal = float(payload["principal_amount"])
        rate = float(payload["interest_rate"])
        tenure = int(payload["tenure_months"])
        first_emi_date = payload["first_emi_date"]
        disbursement_date = payload.get("disbursement_date", first_emi_date)

        summary = calculate_emi_summary(principal, rate, tenure)

        with self.db.transaction() as connection:
            loan_number = self._next_loan_number(connection, date.fromisoformat(disbursement_date))
            cursor = connection.execute(
                """
                INSERT INTO loans (
                    loan_number, customer_id, loan_type_id, principal_amount, interest_rate,
                    tenure_months, emi_amount, processing_fee, total_payable,
                    disbursement_date, first_emi_date, last_emi_date, purpose,
                    collateral_type, collateral_value, collateral_description,
                    status, created_by, created_at, updated_at, remarks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    loan_number,
                    customer_id,
                    loan_type_id,
                    principal,
                    rate,
                    tenure,
                    summary.emi_amount,
                    float(payload.get("processing_fee", 0) or 0),
                    summary.total_payable,
                    disbursement_date,
                    first_emi_date,
                    payload.get("last_emi_date"),
                    payload.get("purpose"),
                    payload.get("collateral_type"),
                    payload.get("collateral_value"),
                    payload.get("collateral_description"),
                    payload.get("status", "pending"),
                    actor_user_id,
                    now_iso(),
                    now_iso(),
                    payload.get("remarks"),
                ),
            )
            loan_id = int(cursor.lastrowid)

            schedule = generate_amortization_schedule(
                principal=principal,
                annual_interest_rate=rate,
                tenure_months=tenure,
                first_due_date=first_emi_date,
            )
            connection.executemany(
                """
                INSERT INTO loan_schedule (
                    loan_id,
                    installment_number,
                    due_date,
                    opening_balance,
                    emi_amount,
                    principal_component,
                    interest_component,
                    closing_balance,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        loan_id,
                        row["installment_number"],
                        row["due_date"],
                        row["opening_balance"],
                        row["emi_amount"],
                        row["principal_component"],
                        row["interest_component"],
                        row["closing_balance"],
                        row["status"],
                    )
                    for row in schedule
                ],
            )

        AUDIT_LOGGER.log_action(actor_user_id, "INSERT", "loans", loan_id, None, payload)
        return loan_id

    def update_loan_status(self, loan_id: int, status: str, actor_user_id: int | None) -> None:
        old_data = self.get_loan(loan_id)
        if not old_data:
            raise ValueError("Loan not found.")

        self.db.execute("UPDATE loans SET status = ?, updated_at = ? WHERE id = ?", (status, now_iso(), loan_id))
        AUDIT_LOGGER.log_action(actor_user_id, "UPDATE", "loans", loan_id, old_data, {"status": status})

    def dashboard_metrics(self) -> dict[str, Any]:
        active = self.db.fetchone("SELECT COUNT(*) AS count, COALESCE(SUM(principal_amount), 0) AS total FROM loans WHERE status IN ('active', 'disbursed') AND is_deleted = 0")
        disbursed = self.db.fetchone("SELECT COALESCE(SUM(principal_amount), 0) AS total FROM loans WHERE status IN ('disbursed', 'active', 'closed') AND is_deleted = 0")
        overdue = self.db.fetchone("SELECT COUNT(*) AS count FROM loan_schedule WHERE status = 'overdue'")
        monthly_collection = self.db.fetchone(
            """
            SELECT COALESCE(SUM(total_paid), 0) AS total
            FROM repayments
            WHERE strftime('%Y-%m', paid_date) = strftime('%Y-%m', 'now')
            """
        )

        return {
            "active_count": int(active["count"] if active else 0),
            "active_total": float(active["total"] if active else 0),
            "disbursed_total": float(disbursed["total"] if disbursed else 0),
            "overdue_count": int(overdue["count"] if overdue else 0),
            "monthly_collection": float(monthly_collection["total"] if monthly_collection else 0),
        }

    def disbursement_trend_last_12_months(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT strftime('%Y-%m', disbursement_date) AS month,
                   COALESCE(SUM(principal_amount), 0) AS amount
            FROM loans
            WHERE disbursement_date IS NOT NULL
              AND disbursement_date >= date('now', '-12 months')
              AND is_deleted = 0
            GROUP BY strftime('%Y-%m', disbursement_date)
            ORDER BY month ASC
            """
        )
        return [dict(row) for row in rows]

    def portfolio_by_type(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT lt.name AS loan_type,
                   COALESCE(SUM(l.principal_amount), 0) AS amount
            FROM loans l
            JOIN loan_types lt ON lt.id = l.loan_type_id
            WHERE l.status IN ('pending', 'approved', 'disbursed', 'active', 'closed')
              AND l.is_deleted = 0
            GROUP BY lt.name
            ORDER BY amount DESC
            """
        )
        return [dict(row) for row in rows]

    def portfolio_management_breakdown(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT
                lt.name AS loan_type,
                COUNT(DISTINCT CASE WHEN l.status IN ('approved', 'disbursed', 'active') THEN l.id END) AS active_loans,
                COALESCE(SUM(CASE WHEN ls.status IN ('pending', 'overdue', 'partial') THEN ls.principal_component ELSE 0 END), 0) AS outstanding_principal,
                COALESCE(SUM(CASE WHEN ls.status = 'overdue' THEN ls.principal_component ELSE 0 END), 0) AS overdue_principal
            FROM loans l
            JOIN loan_types lt ON lt.id = l.loan_type_id
            LEFT JOIN loan_schedule ls ON ls.loan_id = l.id
            WHERE l.is_deleted = 0
              AND l.status IN ('approved', 'disbursed', 'active', 'defaulted', 'closed')
            GROUP BY lt.name
            HAVING
                COALESCE(SUM(CASE WHEN ls.status IN ('pending', 'overdue', 'partial') THEN ls.principal_component ELSE 0 END), 0) > 0
                OR COUNT(DISTINCT CASE WHEN l.status IN ('approved', 'disbursed', 'active') THEN l.id END) > 0
            ORDER BY outstanding_principal DESC, active_loans DESC
            """
        )

        result: list[dict[str, Any]] = []
        for row in rows:
            outstanding = float(row["outstanding_principal"] or 0)
            overdue = float(row["overdue_principal"] or 0)
            delinquency_share = (overdue / outstanding * 100) if outstanding > 0 else 0.0

            result.append(
                {
                    "loan_type": row["loan_type"],
                    "active_loans": int(row["active_loans"] or 0),
                    "outstanding_principal": outstanding,
                    "overdue_principal": overdue,
                    "delinquency_share": delinquency_share,
                }
            )

        return result

    def recent_loan_applications(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT l.loan_number, c.full_name AS customer_name, lt.name AS loan_type,
                   l.principal_amount, l.status, l.created_at
            FROM loans l
            JOIN customers c ON c.id = l.customer_id
            JOIN loan_types lt ON lt.id = l.loan_type_id
            WHERE l.is_deleted = 0
            ORDER BY l.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in rows]

    def todays_due_emis(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT l.id AS loan_id, l.loan_number, c.full_name AS customer_name,
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


LOAN_MODEL = LoanModel()
