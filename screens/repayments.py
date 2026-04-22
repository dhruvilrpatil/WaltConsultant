"""Repayments management screen for WaltConsultant."""

from __future__ import annotations

import csv
from datetime import date
from io import StringIO
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from tkcalendar import DateEntry

from components.button import WaltButton
from components.input import WaltInput, WaltSearchBar
from components.modal import WaltModal
from components.table import WaltTable
from components.toast import WaltToast
from database.connection import get_db_manager
from models.repayment import REPAYMENT_MODEL
from utils.constants import PAYMENT_MODES, ROLE_PERMISSIONS
from utils.pdf_generator import PDF_GENERATOR
from utils.theme import PALETTE


class RepaymentsScreen(tk.Frame):
    def __init__(self, parent, current_user_id: int | None, role: str):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.current_user_id = current_user_id
        self.role = role
        self.db = get_db_manager()

        self._build()
        self.refresh()

    def _can(self, action: str) -> bool:
        return action in ROLE_PERMISSIONS.get(self.role, {}).get("repayments", [])

    def _toast(self, message: str, type: str = "info") -> None:
        WaltToast(self.winfo_toplevel(), message, type).show()

    def _build(self) -> None:
        header = tk.Frame(self, bg=PALETTE.window_bg)
        header.pack(fill="x", padx=20, pady=(16, 10))

        tk.Label(header, text="Repayments", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 22, "bold")).pack(side="left")

        filter_box = tk.Frame(header, bg=PALETTE.window_bg)
        filter_box.pack(side="right")

        self.status_var = tk.StringVar(value="")
        self.status_filter = ttk.Combobox(filter_box, values=["", "pending", "paid", "overdue", "partial", "waived"], textvariable=self.status_var, width=10, style="Walt.TCombobox", state="readonly")
        self.status_filter.pack(side="left", padx=(0, 8))
        self.status_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        self.mode_var = tk.StringVar(value="")
        self.mode_filter = ttk.Combobox(filter_box, values=[""] + PAYMENT_MODES, textvariable=self.mode_var, width=10, style="Walt.TCombobox", state="readonly")
        self.mode_filter.pack(side="left", padx=(0, 8))
        self.mode_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        self.search = WaltSearchBar(filter_box, on_search=lambda _q: self.refresh(), placeholder="Search repayments")
        self.search.pack(side="left", padx=(0, 8))

        self.record_btn = WaltButton(filter_box, text="+ Record Payment", style="primary", command=self._open_record_modal)
        self.record_btn.pack(side="left", padx=(0, 8))
        if not self._can("create"):
            self.record_btn.configure(state="disabled")

        WaltButton(filter_box, text="Bulk CSV Import", style="secondary", command=self._open_bulk_import_modal).pack(side="left")

        body = tk.Frame(self, bg=PALETTE.window_bg)
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.table = WaltTable(
            body,
            columns=[
                ("repayment_id", "Repayment ID", 140),
                ("loan_number", "Loan Number", 150),
                ("customer_name", "Customer", 160),
                ("installment_number", "Inst #", 65),
                ("due_date", "Due Date", 95),
                ("paid_date", "Paid Date", 95),
                ("emi_amount", "EMI Amount", 100),
                ("status", "Status", 90),
                ("payment_mode", "Mode", 80),
            ],
        )
        self.table.pack(fill="both", expand=True)

    def refresh(self) -> None:
        rows = REPAYMENT_MODEL.list_repayments(status=self.status_var.get().strip(), search=self.search.get())

        if self.mode_var.get().strip():
            rows = [row for row in rows if row.get("payment_mode") == self.mode_var.get().strip()]

        self.table.set_data(rows)

    def _loan_choices(self) -> tuple[list[str], dict[str, int]]:
        rows = self.db.fetchall(
            """
            SELECT l.id, l.loan_number, c.full_name
            FROM loans l
            JOIN customers c ON c.id = l.customer_id
            WHERE l.status IN ('active', 'disbursed', 'approved') AND l.is_deleted = 0
            ORDER BY l.created_at DESC
            """
        )
        mapping: dict[str, int] = {}
        choices = []
        for row in rows:
            label = f"{row['loan_number']} | {row['full_name']}"
            mapping[label] = int(row["id"])
            choices.append(label)
        return choices, mapping

    def _open_record_modal(self) -> None:
        modal = WaltModal(self.winfo_toplevel(), "Record Payment", width=620, height=540)

        choices, mapping = self._loan_choices()

        tk.Label(modal.content, text="Loan Number", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w")
        loan_var = tk.StringVar()
        loan_combo = ttk.Combobox(modal.content, values=choices, textvariable=loan_var, style="Walt.TCombobox", state="readonly")
        loan_combo.pack(fill="x", pady=(2, 8))

        details_label = tk.Label(modal.content, text="Select a loan to see due installment", bg=PALETTE.window_bg, fg=PALETTE.text_secondary)
        details_label.pack(anchor="w", pady=(0, 8))

        amount = WaltInput(modal.content, placeholder="Payment Amount")
        amount.pack(fill="x", pady=6)

        mode_var = tk.StringVar(value=PAYMENT_MODES[0])
        ttk.Combobox(modal.content, values=PAYMENT_MODES, textvariable=mode_var, state="readonly", style="Walt.TCombobox").pack(fill="x", pady=6)

        reference = WaltInput(modal.content, placeholder="Transaction Reference")
        reference.pack(fill="x", pady=6)

        tk.Label(modal.content, text="Payment Date", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w", pady=(6, 2))
        paid_date = DateEntry(modal.content, date_pattern="yyyy-mm-dd")
        paid_date.pack(anchor="w")

        remarks = WaltInput(modal.content, placeholder="Remarks")
        remarks.pack(fill="x", pady=6)

        def on_loan_change(_event=None):
            if loan_var.get() not in mapping:
                details_label.configure(text="Select a valid loan")
                return

            loan_id = mapping[loan_var.get()]
            due = self.db.fetchone(
                """
                SELECT ls.installment_number, ls.due_date, ls.emi_amount, c.full_name
                FROM loan_schedule ls
                JOIN loans l ON l.id = ls.loan_id
                JOIN customers c ON c.id = l.customer_id
                WHERE ls.loan_id = ? AND ls.status IN ('pending', 'overdue', 'partial')
                ORDER BY ls.installment_number ASC
                LIMIT 1
                """,
                (loan_id,),
            )
            if not due:
                details_label.configure(text="No outstanding installment for selected loan")
                amount.set("")
                return

            details_label.configure(
                text=f"Customer: {due['full_name']} | Installment #{due['installment_number']} due {due['due_date']} | EMI {due['emi_amount']}"
            )
            amount.set(str(due["emi_amount"]))

        loan_combo.bind("<<ComboboxSelected>>", on_loan_change)

        def save_payment() -> None:
            if loan_var.get() not in mapping:
                self._toast("Select a loan", "warning")
                return

            payload = {
                "loan_id": mapping[loan_var.get()],
                "payment_amount": amount.get(),
                "payment_mode": mode_var.get(),
                "transaction_reference": reference.get(),
                "paid_date": paid_date.get_date().isoformat(),
                "remarks": remarks.get(),
            }

            try:
                repayment_id = REPAYMENT_MODEL.record_payment(payload, self.current_user_id)
                row = self.db.fetchone(
                    """
                    SELECT r.repayment_id, l.loan_number, c.full_name AS customer_name, r.paid_date,
                           r.emi_amount, r.late_fee, r.total_paid, r.payment_mode, r.transaction_reference
                    FROM repayments r
                    JOIN loans l ON l.id = r.loan_id
                    JOIN customers c ON c.id = r.customer_id
                    WHERE r.id = ?
                    """,
                    (repayment_id,),
                )
                if row:
                    receipt_output = Path(__file__).resolve().parents[1] / "exports" / f"receipt_{row['repayment_id']}.pdf"
                    PDF_GENERATOR.generate_receipt(receipt_output, dict(row))
                modal.destroy()
                self.refresh()
                self._toast("Payment recorded and receipt generated", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        WaltButton(modal.footer, text="Cancel", style="secondary", command=modal.destroy).pack(side="right", padx=(8, 0))
        WaltButton(modal.footer, text="Save Payment", style="primary", command=save_payment).pack(side="right")

    def _open_bulk_import_modal(self) -> None:
        modal = WaltModal(self.winfo_toplevel(), "Bulk Payment Import (CSV)", width=760, height=560)

        guidance = (
            "Paste CSV rows with headers: loan_number,payment_amount,paid_date,payment_mode,transaction_reference,remarks\n"
            "Example: WALT-LN-20240115-00001,18000,2026-04-06,UPI,TXN-001,Monthly installment"
        )
        tk.Label(modal.content, text=guidance, bg=PALETTE.window_bg, fg=PALETTE.text_secondary, justify="left", wraplength=700).pack(anchor="w", pady=(0, 8))

        text = tk.Text(modal.content, height=18, bg=PALETTE.input_bg, fg=PALETTE.text_primary, relief="flat", font=("SF Pro Rounded", 11))
        text.pack(fill="both", expand=True)

        result_label = tk.Label(modal.content, text="", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, anchor="w")
        result_label.pack(fill="x", pady=(8, 0))

        def process_csv() -> None:
            raw = text.get("1.0", "end").strip()
            if not raw:
                result_label.configure(text="Paste CSV content first")
                return

            reader = csv.DictReader(StringIO(raw))
            success = 0
            failed = 0

            for row in reader:
                try:
                    loan = self.db.fetchone("SELECT id FROM loans WHERE loan_number = ?", (row["loan_number"],))
                    if not loan:
                        raise ValueError(f"Loan not found: {row['loan_number']}")

                    payload = {
                        "loan_id": int(loan["id"]),
                        "payment_amount": row.get("payment_amount") or "0",
                        "paid_date": row.get("paid_date") or date.today().isoformat(),
                        "payment_mode": row.get("payment_mode") or "UPI",
                        "transaction_reference": row.get("transaction_reference") or "",
                        "remarks": row.get("remarks") or "Bulk CSV import",
                    }
                    REPAYMENT_MODEL.record_payment(payload, self.current_user_id)
                    success += 1
                except Exception:
                    failed += 1

            self.refresh()
            result_label.configure(text=f"Processed rows: {success + failed} | Success: {success} | Failed: {failed}")
            if failed == 0:
                self._toast("Bulk import completed", "success")
            else:
                self._toast("Bulk import completed with some errors", "warning")

        WaltButton(modal.footer, text="Close", style="secondary", command=modal.destroy).pack(side="right", padx=(8, 0))
        WaltButton(modal.footer, text="Import", style="primary", command=process_csv).pack(side="right")
