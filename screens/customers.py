"""Customers management screen for WaltConsultant."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from components.button import WaltButton
from components.card import WaltCard
from components.input import WaltInput, WaltSearchBar
from components.modal import WaltConfirmDialog, WaltModal
from components.table import WaltTable
from components.toast import WaltToast
from database.connection import get_db_manager
from models.customer import CUSTOMER_MODEL
from utils.constants import ROLE_PERMISSIONS
from utils.theme import PALETTE


class CustomersScreen(tk.Frame):
    def __init__(self, parent, current_user_id: int | None, role: str):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.current_user_id = current_user_id
        self.role = role
        self.selected_row: dict | None = None

        self.db = get_db_manager()

        self._build()
        self.refresh()

    def _can(self, action: str) -> bool:
        return action in ROLE_PERMISSIONS.get(self.role, {}).get("customers", [])

    def _build(self) -> None:
        header = tk.Frame(self, bg=PALETTE.window_bg)
        header.pack(fill="x", padx=20, pady=(16, 10))

        title_row = tk.Frame(header, bg=PALETTE.window_bg)
        title_row.pack(fill="x")
        tk.Label(title_row, text="Customers", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 22, "bold")).pack(side="left")

        controls_row = tk.Frame(header, bg=PALETTE.window_bg)
        controls_row.pack(fill="x", pady=(10, 0))

        left_controls = tk.Frame(controls_row, bg=PALETTE.window_bg)
        left_controls.pack(side="left")

        self.add_btn = WaltButton(left_controls, text="+ Add Customer", style="primary", command=self._open_add_modal)
        self.add_btn.pack(side="left")
        if not self._can("create"):
            self.add_btn.configure(state="disabled")

        search_holder = tk.Frame(controls_row, bg=PALETTE.window_bg)
        search_holder.pack(side="right", padx=(10, 0))
        self.search = WaltSearchBar(search_holder, on_search=self._on_search, placeholder="Search customers")
        self.search.pack(side="right")
        self.search.entry.configure(width=20)

        body_card = WaltCard(self, padding=12, radius=18, outer_bg=PALETTE.window_bg)
        body_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        body = body_card.content

        self.table = WaltTable(
            body,
            columns=[
                ("customer_id", "Customer ID", 130),
                ("full_name", "Full Name", 170),
                ("phone", "Phone", 120),
                ("city", "City", 120),
                ("active_loans", "Active Loans", 90),
                ("credit_score", "Credit Score", 90),
                ("status", "Status", 90),
            ],
            on_row_click=self._on_row_select,
        )
        self.table.pack(fill="both", expand=True)

        actions = tk.Frame(body, bg=PALETTE.window_bg)
        actions.pack(fill="x", pady=(10, 0))

        self.view_btn = WaltButton(actions, text="View", style="secondary", command=self._open_detail_panel)
        self.view_btn.pack(side="left")

        self.edit_btn = WaltButton(actions, text="Edit", style="secondary", command=self._open_edit_modal)
        self.edit_btn.pack(side="left", padx=(8, 0))
        if not self._can("update"):
            self.edit_btn.configure(state="disabled")

        self.delete_btn = WaltButton(actions, text="Delete", style="destructive", command=self._confirm_delete)
        self.delete_btn.pack(side="left", padx=(8, 0))
        if not self._can("delete"):
            self.delete_btn.configure(state="disabled")

        self.detail_panel = WaltCard(self, padding=0, radius=18, outer_bg=PALETTE.window_bg)
        self.detail_panel.place(relx=1.0, rely=0, relheight=1.0, width=0, anchor="ne")
        self.detail_content = self.detail_panel.content

    def _on_search(self, text: str) -> None:
        self.refresh(text)

    def _on_row_select(self, row: dict) -> None:
        self.selected_row = row

    def refresh(self, search: str = "") -> None:
        data = CUSTOMER_MODEL.list_customers(search=search)
        table_rows = []
        for row in data:
            row = dict(row)
            row["status"] = "Active" if int(row.get("is_active", 1)) == 1 else "Inactive"
            table_rows.append(row)
        self.table.set_data(table_rows)

    def _show_toast(self, message: str, type: str = "info") -> None:
        WaltToast(self.winfo_toplevel(), message, type).show()

    def _open_add_modal(self) -> None:
        modal = WaltModal(self.winfo_toplevel(), "Add Customer", width=560, height=560)

        full_name = WaltInput(modal.content, placeholder="Full Name")
        full_name.pack(fill="x", pady=8)
        email = WaltInput(modal.content, placeholder="Email")
        email.pack(fill="x", pady=8)
        phone = WaltInput(modal.content, placeholder="Phone")
        phone.pack(fill="x", pady=8)
        city = WaltInput(modal.content, placeholder="City")
        city.pack(fill="x", pady=8)
        state = WaltInput(modal.content, placeholder="State")
        state.pack(fill="x", pady=8)
        pincode = WaltInput(modal.content, placeholder="Pincode")
        pincode.pack(fill="x", pady=8)

        def save_customer() -> None:
            try:
                CUSTOMER_MODEL.create_customer(
                    {
                        "full_name": full_name.get(),
                        "email": email.get(),
                        "phone": phone.get(),
                        "city": city.get(),
                        "state": state.get(),
                        "pincode": pincode.get(),
                        "country": "India",
                    },
                    self.current_user_id,
                )
                modal.destroy()
                self.refresh(self.search.get())
                self._show_toast("Customer added successfully", "success")
            except Exception as error:
                self._show_toast(str(error), "danger")

        WaltButton(modal.footer, text="Cancel", style="secondary", command=modal.destroy).pack(side="right", padx=(8, 0))
        WaltButton(modal.footer, text="Save", style="primary", command=save_customer).pack(side="right")

    def _resolve_selected_customer_id(self) -> int | None:
        if not self.selected_row:
            return None
        customer_code = self.selected_row.get("customer_id")
        row = self.db.fetchone("SELECT id FROM customers WHERE customer_id = ?", (customer_code,))
        return int(row["id"]) if row else None

    def _open_edit_modal(self) -> None:
        customer_id = self._resolve_selected_customer_id()
        if not customer_id:
            self._show_toast("Select a customer first", "warning")
            return

        customer = CUSTOMER_MODEL.get_customer(customer_id)
        if not customer:
            self._show_toast("Customer not found", "danger")
            return

        modal = WaltModal(self.winfo_toplevel(), "Edit Customer", width=560, height=560)

        full_name = WaltInput(modal.content, placeholder="Full Name")
        full_name.pack(fill="x", pady=8)
        full_name.set(customer.get("full_name", ""))

        email = WaltInput(modal.content, placeholder="Email")
        email.pack(fill="x", pady=8)
        email.set(customer.get("email", ""))

        phone = WaltInput(modal.content, placeholder="Phone")
        phone.pack(fill="x", pady=8)
        phone.set(customer.get("phone", ""))

        city = WaltInput(modal.content, placeholder="City")
        city.pack(fill="x", pady=8)
        city.set(customer.get("city", ""))

        state = WaltInput(modal.content, placeholder="State")
        state.pack(fill="x", pady=8)
        state.set(customer.get("state", ""))

        pincode = WaltInput(modal.content, placeholder="Pincode")
        pincode.pack(fill="x", pady=8)
        pincode.set(customer.get("pincode", ""))

        def update_customer() -> None:
            try:
                CUSTOMER_MODEL.update_customer(
                    customer_id,
                    {
                        "full_name": full_name.get(),
                        "email": email.get(),
                        "phone": phone.get(),
                        "city": city.get(),
                        "state": state.get(),
                        "pincode": pincode.get(),
                    },
                    self.current_user_id,
                )
                modal.destroy()
                self.refresh(self.search.get())
                self._show_toast("Customer updated", "success")
            except Exception as error:
                self._show_toast(str(error), "danger")

        WaltButton(modal.footer, text="Cancel", style="secondary", command=modal.destroy).pack(side="right", padx=(8, 0))
        WaltButton(modal.footer, text="Update", style="primary", command=update_customer).pack(side="right")

    def _confirm_delete(self) -> None:
        customer_id = self._resolve_selected_customer_id()
        if not customer_id:
            self._show_toast("Select a customer first", "warning")
            return

        def delete_now() -> None:
            try:
                CUSTOMER_MODEL.deactivate_customer(customer_id, self.current_user_id)
                self.refresh(self.search.get())
                self._show_toast("Customer deactivated", "success")
            except Exception as error:
                self._show_toast(str(error), "danger")

        WaltConfirmDialog(self.winfo_toplevel(), "Delete Customer", "Are you sure you want to deactivate this customer?", delete_now)

    def _open_detail_panel(self) -> None:
        customer_id = self._resolve_selected_customer_id()
        if not customer_id:
            self._show_toast("Select a customer first", "warning")
            return

        customer = CUSTOMER_MODEL.get_customer(customer_id)
        if not customer:
            self._show_toast("Customer details not found", "danger")
            return

        for child in self.detail_content.winfo_children():
            child.destroy()

        tk.Label(self.detail_content, text=customer["full_name"], bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 16, "bold")).pack(anchor="w", padx=16, pady=(16, 4))
        tk.Label(self.detail_content, text=customer["customer_id"], bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 11)).pack(anchor="w", padx=16)

        info = tk.Frame(self.detail_content, bg=PALETTE.window_bg)
        info.pack(fill="x", padx=16, pady=12)
        for label, value in [
            ("Email", customer.get("email", "-")),
            ("Phone", customer.get("phone", "-")),
            ("City", customer.get("city", "-")),
            ("State", customer.get("state", "-")),
            ("Credit Score", customer.get("credit_score", "-")),
        ]:
            row = tk.Frame(info, bg=PALETTE.window_bg)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{label}:", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, width=12, anchor="w", font=("SF Pro Rounded", 10)).pack(side="left")
            tk.Label(row, text=str(value), bg=PALETTE.window_bg, fg=PALETTE.text_primary, anchor="w", font=("SF Pro Rounded", 10)).pack(side="left")

        tabs = ttk.Notebook(self.detail_content, style="Walt.TNotebook")
        tabs.pack(fill="both", expand=True, padx=12, pady=(8, 12))

        overview_tab = tk.Frame(tabs, bg=PALETTE.window_bg)
        loans_tab = tk.Frame(tabs, bg=PALETTE.window_bg)
        repayments_tab = tk.Frame(tabs, bg=PALETTE.window_bg)
        docs_tab = tk.Frame(tabs, bg=PALETTE.window_bg)
        activity_tab = tk.Frame(tabs, bg=PALETTE.window_bg)

        tabs.add(overview_tab, text="Overview")
        tabs.add(loans_tab, text="Loans")
        tabs.add(repayments_tab, text="Repayments")
        tabs.add(docs_tab, text="Documents")
        tabs.add(activity_tab, text="Activity")

        tk.Label(overview_tab, text=customer.get("notes") or "No notes available.", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, wraplength=410, justify="left").pack(anchor="w", padx=8, pady=8)

        loans = self.db.fetchall(
            "SELECT loan_number, principal_amount, status FROM loans WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        )
        if loans:
            for loan in loans:
                tk.Label(loans_tab, text=f"{loan['loan_number']} | Rs {float(loan['principal_amount']):,.2f} | {loan['status']}", bg=PALETTE.window_bg, fg=PALETTE.text_primary, anchor="w").pack(fill="x", padx=8, pady=2)
        else:
            tk.Label(loans_tab, text="No loans", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w", padx=8, pady=8)

        repayments = self.db.fetchall(
            "SELECT repayment_id, total_paid, paid_date FROM repayments WHERE customer_id = ? ORDER BY created_at DESC LIMIT 10",
            (customer_id,),
        )
        if repayments:
            for repayment in repayments:
                tk.Label(repayments_tab, text=f"{repayment['repayment_id']} | Rs {float(repayment['total_paid']):,.2f} | {repayment['paid_date']}", bg=PALETTE.window_bg, fg=PALETTE.text_primary, anchor="w").pack(fill="x", padx=8, pady=2)
        else:
            tk.Label(repayments_tab, text="No repayments", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w", padx=8, pady=8)

        documents = self.db.fetchall(
            "SELECT document_name, document_type, uploaded_at FROM documents WHERE reference_type = 'customer' AND reference_id = ? ORDER BY uploaded_at DESC",
            (customer_id,),
        )
        if documents:
            for doc in documents:
                tk.Label(docs_tab, text=f"{doc['document_name']} ({doc['document_type']})", bg=PALETTE.window_bg, fg=PALETTE.text_primary, anchor="w").pack(fill="x", padx=8, pady=2)
        else:
            tk.Label(docs_tab, text="No documents", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w", padx=8, pady=8)

        activity = self.db.fetchall(
            "SELECT action, timestamp FROM audit_log WHERE module = 'customers' AND record_id = ? ORDER BY timestamp DESC LIMIT 20",
            (customer_id,),
        )
        if activity:
            for item in activity:
                tk.Label(activity_tab, text=f"{item['timestamp']} - {item['action']}", bg=PALETTE.window_bg, fg=PALETTE.text_primary, anchor="w").pack(fill="x", padx=8, pady=2)
        else:
            tk.Label(activity_tab, text="No activity", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w", padx=8, pady=8)

        self._animate_panel(open_panel=True)

    def _animate_panel(self, open_panel: bool) -> None:
        target = 480 if open_panel else 0
        current = self.detail_panel.winfo_width()
        step = 40 if open_panel else -40

        def run() -> None:
            nonlocal current
            current += step
            if (open_panel and current >= target) or (not open_panel and current <= target):
                current = target
            self.detail_panel.place_configure(width=current)
            if current != target:
                self.after(12, run)

        run()
