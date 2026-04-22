"""Loans management screen for WaltConsultant."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from tkcalendar import DateEntry

from components.button import WaltButton
from components.card import WaltCard
from components.input import WaltInput, WaltSearchBar
from components.modal import WaltModal
from components.table import WaltTable
from components.toast import WaltToast
from database.connection import get_db_manager
from models.loan import LOAN_MODEL
from utils.calculations import calculate_emi_summary
from utils.constants import ROLE_PERMISSIONS
from utils.formatters import format_inr, safe_float, safe_int
from utils.pdf_generator import PDF_GENERATOR
from utils.theme import PALETTE


class LoansScreen(tk.Frame):
    def __init__(self, parent, current_user_id: int | None, role: str):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.current_user_id = current_user_id
        self.role = role
        self.db = get_db_manager()
        self.selected_loan_number: str | None = None

        self._build()
        self.refresh()

    def _can(self, action: str) -> bool:
        return action in ROLE_PERMISSIONS.get(self.role, {}).get("loans", [])

    def _toast(self, message: str, type: str = "info") -> None:
        WaltToast(self.winfo_toplevel(), message, type).show()

    def _build(self) -> None:
        header = tk.Frame(self, bg=PALETTE.window_bg)
        header.pack(fill="x", padx=20, pady=(16, 10))

        tk.Label(header, text="Loans", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 22, "bold")).pack(side="left")

        filter_frame = tk.Frame(header, bg=PALETTE.window_bg)
        filter_frame.pack(side="right")

        self.status_var = tk.StringVar(value="")
        self.status_filter = ttk.Combobox(filter_frame, values=["", "pending", "approved", "disbursed", "active", "closed", "rejected", "defaulted"], textvariable=self.status_var, width=12, style="Walt.TCombobox", state="readonly")
        self.status_filter.pack(side="left", padx=(0, 8))
        self.status_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        self.type_var = tk.StringVar(value="")
        self.type_filter = ttk.Combobox(filter_frame, values=[""], textvariable=self.type_var, width=16, style="Walt.TCombobox", state="readonly")
        self.type_filter.pack(side="left", padx=(0, 8))
        self.type_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        self.search = WaltSearchBar(filter_frame, on_search=lambda _q: self.refresh(), placeholder="Search loans")
        self.search.pack(side="left", padx=(0, 8))

        self.new_btn = WaltButton(filter_frame, text="+ New Loan", style="primary", command=self._open_new_modal)
        self.new_btn.pack(side="left")
        if not self._can("create"):
            self.new_btn.configure(state="disabled")

        body_card = WaltCard(self, padding=12, radius=18, outer_bg=PALETTE.window_bg)
        body_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        body = body_card.content

        self.table = WaltTable(
            body,
            columns=[
                ("loan_number", "Loan Number", 170),
                ("customer_name", "Customer", 170),
                ("loan_type", "Loan Type", 130),
                ("principal_amount", "Principal", 120),
                ("interest_rate", "Rate", 70),
                ("tenure_months", "Tenure", 70),
                ("emi_amount", "EMI", 110),
                ("disbursement_date", "Disbursed", 100),
                ("status", "Status", 90),
            ],
            on_row_click=self._on_row_select,
        )
        self.table.pack(fill="both", expand=True)

        actions = tk.Frame(body, bg=PALETTE.window_bg)
        actions.pack(fill="x", pady=(10, 0))
        WaltButton(actions, text="View", style="secondary", command=self._open_detail).pack(side="left")

        self.approve_btn = WaltButton(actions, text="Approve", style="secondary", command=lambda: self._update_status("approved"))
        self.approve_btn.pack(side="left", padx=(8, 0))
        if not self._can("approve"):
            self.approve_btn.configure(state="disabled")

        self.disburse_btn = WaltButton(actions, text="Disburse", style="secondary", command=lambda: self._update_status("disbursed"))
        self.disburse_btn.pack(side="left", padx=(8, 0))
        if not self._can("disburse"):
            self.disburse_btn.configure(state="disabled")

        self.close_btn = WaltButton(actions, text="Close", style="secondary", command=lambda: self._update_status("closed"))
        self.close_btn.pack(side="left", padx=(8, 0))
        if not self._can("close"):
            self.close_btn.configure(state="disabled")

        WaltButton(actions, text="Generate Statement", style="secondary", command=self._generate_statement).pack(side="left", padx=(8, 0))

        self.detail_panel = WaltCard(self, padding=0, radius=18, outer_bg=PALETTE.window_bg)
        self.detail_panel.place(relx=1.0, rely=0, relheight=1.0, width=0, anchor="ne")
        self.detail_content = self.detail_panel.content

    def _on_row_select(self, row: dict) -> None:
        self.selected_loan_number = str(row.get("loan_number"))

    def _selected_loan_id(self) -> int | None:
        if not self.selected_loan_number:
            return None
        row = self.db.fetchone("SELECT id FROM loans WHERE loan_number = ?", (self.selected_loan_number,))
        return int(row["id"]) if row else None

    def refresh(self) -> None:
        rows = LOAN_MODEL.list_loans(status=self.status_var.get().strip(), search=self.search.get())
        loan_type_filter = self.type_var.get().strip()
        if loan_type_filter:
            rows = [row for row in rows if row["loan_type"] == loan_type_filter]

        table_rows = []
        for row in rows:
            row = dict(row)
            row["principal_amount"] = format_inr(float(row["principal_amount"]))
            row["interest_rate"] = f"{float(row['interest_rate']):.2f}%"
            row["emi_amount"] = format_inr(float(row["emi_amount"]))
            table_rows.append(row)

        self.table.set_data(table_rows)
        self._load_loan_types()

    def _load_loan_types(self) -> None:
        rows = self.db.fetchall("SELECT name FROM loan_types ORDER BY name")
        values = [""] + [row["name"] for row in rows]
        self.type_filter.configure(values=values)

    def _open_new_modal(self) -> None:
        modal = WaltModal(self.winfo_toplevel(), "New Loan", width=720, height=620)

        row1 = tk.Frame(modal.content, bg=PALETTE.window_bg)
        row1.pack(fill="x", pady=6)

        customer_values = []
        customer_rows = self.db.fetchall("SELECT id, customer_id, full_name FROM customers WHERE is_active = 1 ORDER BY full_name")
        for c in customer_rows:
            customer_values.append(f"{c['id']} | {c['customer_id']} | {c['full_name']}")

        tk.Label(row1, text="Customer", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w")
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(row1, values=customer_values, textvariable=customer_var, style="Walt.TCombobox", state="readonly")
        customer_combo.pack(fill="x", pady=(2, 8))

        loan_types = self.db.fetchall("SELECT id, name, base_interest_rate FROM loan_types ORDER BY name")
        loan_values = [f"{row['id']} | {row['name']}" for row in loan_types]

        tk.Label(row1, text="Loan Type", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w")
        loan_type_var = tk.StringVar()
        loan_combo = ttk.Combobox(row1, values=loan_values, textvariable=loan_type_var, style="Walt.TCombobox", state="readonly")
        loan_combo.pack(fill="x", pady=(2, 8))

        principal = WaltInput(row1, placeholder="Principal Amount")
        principal.pack(fill="x", pady=6)
        interest = WaltInput(row1, placeholder="Interest Rate (annual %)")
        interest.pack(fill="x", pady=6)
        tenure = WaltInput(row1, placeholder="Tenure (months)")
        tenure.pack(fill="x", pady=6)

        date_row = tk.Frame(row1, bg=PALETTE.window_bg)
        date_row.pack(fill="x", pady=6)
        tk.Label(date_row, text="First EMI Date", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w")
        first_emi = DateEntry(
            date_row,
            date_pattern="yyyy-mm-dd",
            style="Walt.DateEntry",
            width=16,
            font=("SF Pro Rounded", 12),
            background=PALETTE.primary,
            foreground=PALETTE.text_primary,
            borderwidth=1,
            headersbackground=PALETTE.input_bg,
            headersforeground=PALETTE.text_primary,
            normalbackground=PALETTE.input_bg,
            normalforeground=PALETTE.text_primary,
            weekendbackground=PALETTE.input_bg,
            weekendforeground=PALETTE.text_primary,
        )
        first_emi.pack(anchor="w", pady=(2, 0))

        purpose = WaltInput(row1, placeholder="Purpose")
        purpose.pack(fill="x", pady=6)
        collateral_type = WaltInput(row1, placeholder="Collateral Type")
        collateral_type.pack(fill="x", pady=6)
        collateral_value = WaltInput(row1, placeholder="Collateral Value")
        collateral_value.pack(fill="x", pady=6)

        emi_preview = tk.Label(row1, text="EMI: - | Interest: - | Total: -", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 11))
        emi_preview.pack(anchor="w", pady=8)

        def recalc_preview(_event=None):
            p = safe_float(principal.get())
            r = safe_float(interest.get())
            t = safe_int(tenure.get())
            if p <= 0 or t <= 0:
                emi_preview.configure(text="EMI: - | Interest: - | Total: -")
                return
            try:
                summary = calculate_emi_summary(p, r, t)
                emi_preview.configure(
                    text=f"EMI: {format_inr(summary.emi_amount)} | Interest: {format_inr(summary.total_interest)} | Total: {format_inr(summary.total_payable)}"
                )
            except Exception:
                emi_preview.configure(text="EMI: - | Interest: - | Total: -")

        principal.entry.bind("<KeyRelease>", recalc_preview)
        interest.entry.bind("<KeyRelease>", recalc_preview)
        tenure.entry.bind("<KeyRelease>", recalc_preview)

        def on_loan_type_change(_event=None):
            raw = loan_type_var.get()
            if not raw:
                return
            loan_type_id = int(raw.split("|", 1)[0].strip())
            selected = next((row for row in loan_types if int(row["id"]) == loan_type_id), None)
            if selected and not interest.get():
                interest.set(str(selected["base_interest_rate"]))
                recalc_preview()

        loan_combo.bind("<<ComboboxSelected>>", on_loan_type_change)

        def save_loan() -> None:
            try:
                customer_id = int(customer_var.get().split("|", 1)[0].strip())
                loan_type_id = int(loan_type_var.get().split("|", 1)[0].strip())
            except Exception:
                self._toast("Select customer and loan type", "warning")
                return

            payload = {
                "customer_id": customer_id,
                "loan_type_id": loan_type_id,
                "principal_amount": safe_float(principal.get()),
                "interest_rate": safe_float(interest.get()),
                "tenure_months": safe_int(tenure.get()),
                "first_emi_date": first_emi.get_date().isoformat(),
                "disbursement_date": first_emi.get_date().isoformat(),
                "purpose": purpose.get(),
                "collateral_type": collateral_type.get(),
                "collateral_value": safe_float(collateral_value.get()),
                "status": "pending",
            }

            try:
                LOAN_MODEL.create_loan(payload, self.current_user_id)
                modal.destroy()
                self.refresh()
                self._toast("Loan created successfully", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        WaltButton(modal.footer, text="Cancel", style="secondary", command=modal.destroy).pack(side="right", padx=(8, 0))
        WaltButton(modal.footer, text="Submit for Approval", style="primary", command=save_loan).pack(side="right")

    def _update_status(self, status: str) -> None:
        loan_id = self._selected_loan_id()
        if not loan_id:
            self._toast("Select a loan first", "warning")
            return
        try:
            LOAN_MODEL.update_loan_status(loan_id, status, self.current_user_id)
            self.refresh()
            self._toast(f"Loan moved to {status}", "success")
        except Exception as error:
            self._toast(str(error), "danger")

    def _open_detail(self) -> None:
        loan_id = self._selected_loan_id()
        if not loan_id:
            self._toast("Select a loan first", "warning")
            return

        details = LOAN_MODEL.get_loan(loan_id)
        if not details:
            self._toast("Loan details not found", "danger")
            return

        schedule = LOAN_MODEL.get_loan_schedule(loan_id)

        for child in self.detail_content.winfo_children():
            child.destroy()

        tk.Label(self.detail_content, text=details["loan_number"], bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 16, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
        tk.Label(self.detail_content, text=f"{details['customer_name']} | {details['loan_type_name']}", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 11)).pack(anchor="w", padx=16, pady=(0, 10))

        summary_frame = tk.Frame(self.detail_content, bg=PALETTE.window_bg)
        summary_frame.pack(fill="x", padx=16)
        for label, value in [
            ("Principal", format_inr(float(details["principal_amount"]))),
            ("Total Payable", format_inr(float(details.get("total_payable") or 0))),
            ("EMI", format_inr(float(details["emi_amount"]))),
            ("Status", details["status"]),
        ]:
            row = tk.Frame(summary_frame, bg=PALETTE.window_bg)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{label}:", width=14, bg=PALETTE.window_bg, fg=PALETTE.text_secondary, anchor="w").pack(side="left")
            tk.Label(row, text=value, bg=PALETTE.window_bg, fg=PALETTE.text_primary, anchor="w").pack(side="left")

        tk.Label(self.detail_content, text="Amortization Schedule", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        schedule_table = WaltTable(
            self.detail_content,
            columns=[
                ("installment_number", "#", 36),
                ("due_date", "Due Date", 90),
                ("opening_balance", "Opening", 90),
                ("emi_amount", "EMI", 90),
                ("principal_component", "Principal", 90),
                ("interest_component", "Interest", 90),
                ("closing_balance", "Closing", 90),
                ("status", "Status", 74),
            ],
        )
        schedule_table.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        formatted = []
        for row in schedule:
            formatted.append(
                {
                    **row,
                    "opening_balance": format_inr(float(row["opening_balance"])),
                    "emi_amount": format_inr(float(row["emi_amount"])),
                    "principal_component": format_inr(float(row["principal_component"])),
                    "interest_component": format_inr(float(row["interest_component"])),
                    "closing_balance": format_inr(float(row["closing_balance"])),
                }
            )
        schedule_table.set_data(formatted)

        self._animate_panel(True)

    def _animate_panel(self, open_panel: bool) -> None:
        target = 520 if open_panel else 0
        current = self.detail_panel.winfo_width()
        step = 40 if open_panel else -40

        def run():
            nonlocal current
            current += step
            if (open_panel and current >= target) or (not open_panel and current <= target):
                current = target
            self.detail_panel.place_configure(width=current)
            if current != target:
                self.after(12, run)

        run()

    def _generate_statement(self) -> None:
        loan_id = self._selected_loan_id()
        if not loan_id:
            self._toast("Select a loan first", "warning")
            return

        details = LOAN_MODEL.get_loan(loan_id)
        if not details:
            self._toast("Loan not found", "danger")
            return

        schedule = LOAN_MODEL.get_loan_schedule(loan_id)
        output_path = Path(__file__).resolve().parents[1] / "exports" / f"statement_{details['loan_number']}.pdf"

        try:
            PDF_GENERATOR.generate_loan_statement(output_path, details, schedule)
            self._toast(f"Statement exported: {output_path.name}", "success")
        except Exception as error:
            self._toast(str(error), "danger")
