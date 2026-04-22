"""Settings screen for WaltConsultant."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

from components.button import WaltButton
from components.card import WaltCard
from components.input import WaltInput
from components.modal import WaltConfirmDialog, WaltModal
from components.table import WaltTable
from components.toast import WaltToast
from database.connection import get_db_manager
from models.user import USER_MODEL
from utils.auth import AUTH_SERVICE
from utils.constants import ROLE_PERMISSIONS
from utils.theme import PALETTE, get_theme_mode, save_theme_mode


class SettingsScreen(tk.Frame):
    def __init__(self, parent, current_user_id: int | None, role: str):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.current_user_id = current_user_id
        self.role = role
        self.db = get_db_manager()

        self._build()

    def _can_admin(self) -> bool:
        return self.role == "admin"

    def _toast(self, message: str, type: str = "info") -> None:
        WaltToast(self.winfo_toplevel(), message, type).show()

    def _build(self) -> None:
        tk.Label(self, text="Settings", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 22, "bold")).pack(anchor="w", padx=20, pady=(16, 10))

        notebook = ttk.Notebook(self, style="Walt.TNotebook")
        notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.profile_tab = tk.Frame(notebook, bg=PALETTE.window_bg)
        self.appearance_tab = tk.Frame(notebook, bg=PALETTE.window_bg)
        self.company_tab = tk.Frame(notebook, bg=PALETTE.window_bg)
        self.loan_types_tab = tk.Frame(notebook, bg=PALETTE.window_bg)
        self.users_tab = tk.Frame(notebook, bg=PALETTE.window_bg)
        self.audit_tab = tk.Frame(notebook, bg=PALETTE.window_bg)
        self.database_tab = tk.Frame(notebook, bg=PALETTE.window_bg)

        notebook.add(self.profile_tab, text="My Profile")
        notebook.add(self.appearance_tab, text="Appearance")
        notebook.add(self.company_tab, text="Company Settings")
        notebook.add(self.loan_types_tab, text="Loan Types")
        notebook.add(self.users_tab, text="User Management")
        notebook.add(self.audit_tab, text="Audit Log")
        notebook.add(self.database_tab, text="Database")

        self._build_profile_tab()
        self._build_appearance_tab()
        self._build_company_tab()
        self._build_loan_types_tab()
        self._build_users_tab()
        self._build_audit_tab()
        self._build_database_tab()

        if not self._can_admin():
            notebook.hide(self.users_tab)

    def _build_profile_tab(self) -> None:
        user = USER_MODEL.get_user_by_id(self.current_user_id) if self.current_user_id else None
        if not user:
            tk.Label(self.profile_tab, text="User profile not found", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w", padx=14, pady=14)
            return

        form_card = WaltCard(self.profile_tab, padding=14, radius=18, outer_bg=PALETTE.window_bg)
        form_card.pack(fill="x", padx=14, pady=14)
        form = form_card.content

        full_name = WaltInput(form, placeholder="Full Name")
        full_name.pack(fill="x", pady=6)
        full_name.set(str(user.get("full_name", "")))

        phone = WaltInput(form, placeholder="Phone")
        phone.pack(fill="x", pady=6)
        phone.set(str(user.get("phone", "")))

        city = WaltInput(form, placeholder="City")
        city.pack(fill="x", pady=6)
        city.set(str(user.get("city", "")))

        state = WaltInput(form, placeholder="State")
        state.pack(fill="x", pady=6)
        state.set(str(user.get("state", "")))

        def save_profile() -> None:
            try:
                self.db.execute(
                    "UPDATE users SET full_name = ?, phone = ?, city = ?, state = ? WHERE id = ?",
                    (full_name.get(), phone.get(), city.get(), state.get(), self.current_user_id),
                )
                self._toast("Profile updated", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        btn_row = tk.Frame(form, bg=PALETTE.window_bg)
        btn_row.pack(fill="x", pady=(8, 0))
        WaltButton(btn_row, text="Save Profile", style="primary", command=save_profile).pack(side="left")

        old_pwd = WaltInput(form, placeholder="Current Password", show_password_toggle=True, is_password=True)
        old_pwd.pack(fill="x", pady=(22, 6))

        new_pwd = WaltInput(form, placeholder="New Password", show_password_toggle=True, is_password=True)
        new_pwd.pack(fill="x", pady=6)

        def change_password() -> None:
            row = self.db.fetchone("SELECT password_hash FROM users WHERE id = ?", (self.current_user_id,))
            if not row or not AUTH_SERVICE.verify_password(old_pwd.get(), row["password_hash"]):
                self._toast("Current password is incorrect", "danger")
                return
            self.db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (AUTH_SERVICE.hash_password(new_pwd.get()), self.current_user_id))
            self._toast("Password updated", "success")

        WaltButton(form, text="Change Password", style="secondary", command=change_password).pack(anchor="w", pady=(8, 0))

    def _build_company_tab(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS company_settings (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                company_name TEXT,
                logo BLOB,
                address TEXT
            )
            """
        )
        row = self.db.fetchone("SELECT company_name, address FROM company_settings WHERE id = 1")

        form_card = WaltCard(self.company_tab, padding=14, radius=18, outer_bg=PALETTE.window_bg)
        form_card.pack(fill="x", padx=14, pady=14)
        form = form_card.content

        company_name = WaltInput(form, placeholder="Company Name")
        company_name.pack(fill="x", pady=6)
        company_name.set(row["company_name"] if row else "WaltConsultant")

        address = WaltInput(form, placeholder="Company Address")
        address.pack(fill="x", pady=6)
        address.set(row["address"] if row else "")

        def save_company() -> None:
            try:
                self.db.execute(
                    """
                    INSERT INTO company_settings (id, company_name, address)
                    VALUES (1, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET company_name = excluded.company_name, address = excluded.address
                    """,
                    (company_name.get(), address.get()),
                )
                self._toast("Company settings updated", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        WaltButton(form, text="Save Company Settings", style="primary", command=save_company).pack(anchor="w", pady=(8, 0))

    def _build_appearance_tab(self) -> None:
        card = WaltCard(self.appearance_tab, padding=14, radius=18, outer_bg=PALETTE.window_bg)
        card.pack(fill="x", padx=14, pady=14)
        content = card.content

        tk.Label(content, text="Theme", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 14, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(content, text="Choose between Light and Dark mode. Restart is required for full app-wide refresh.", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, justify="left", wraplength=760).pack(anchor="w", pady=(0, 12))

        row = tk.Frame(content, bg=PALETTE.window_bg)
        row.pack(fill="x")

        tk.Label(row, text="Theme Mode", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(side="left", padx=(0, 8))
        self.theme_mode_var = tk.StringVar(value=get_theme_mode())
        ttk.Combobox(
            row,
            values=["light", "dark"],
            textvariable=self.theme_mode_var,
            state="readonly",
            width=14,
            style="Walt.TCombobox",
        ).pack(side="left")

        def apply_theme_mode() -> None:
            mode = self.theme_mode_var.get().strip().lower()
            try:
                save_theme_mode(mode)
                self._toast(f"{mode.title()} theme saved. Restart the app to apply everywhere.", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        WaltButton(content, text="Apply Theme", style="primary", command=apply_theme_mode).pack(anchor="w", pady=(12, 0))

    def _build_loan_types_tab(self) -> None:
        frame_card = WaltCard(self.loan_types_tab, padding=14, radius=18, outer_bg=PALETTE.window_bg)
        frame_card.pack(fill="both", expand=True, padx=14, pady=14)
        frame = frame_card.content

        top = tk.Frame(frame, bg=PALETTE.window_bg)
        top.pack(fill="x")
        WaltButton(top, text="Add Loan Type", style="primary", command=self._open_add_loan_type_modal).pack(side="left")

        self.loan_types_table = WaltTable(
            frame,
            columns=[
                ("id", "ID", 50),
                ("name", "Name", 170),
                ("min_amount", "Min", 120),
                ("max_amount", "Max", 120),
                ("base_interest_rate", "Base Rate", 100),
                ("processing_fee_percent", "Fee %", 80),
            ],
        )
        self.loan_types_table.pack(fill="both", expand=True, pady=(10, 0))
        self._refresh_loan_types()

    def _refresh_loan_types(self) -> None:
        rows = self.db.fetchall("SELECT id, name, min_amount, max_amount, base_interest_rate, processing_fee_percent FROM loan_types ORDER BY name")
        self.loan_types_table.set_data([dict(row) for row in rows])

    def _open_add_loan_type_modal(self) -> None:
        modal = WaltModal(self.winfo_toplevel(), "Add Loan Type", width=560, height=520)

        name = WaltInput(modal.content, placeholder="Loan Type Name")
        name.pack(fill="x", pady=6)
        min_amount = WaltInput(modal.content, placeholder="Min Amount")
        min_amount.pack(fill="x", pady=6)
        max_amount = WaltInput(modal.content, placeholder="Max Amount")
        max_amount.pack(fill="x", pady=6)
        min_tenure = WaltInput(modal.content, placeholder="Min Tenure (months)")
        min_tenure.pack(fill="x", pady=6)
        max_tenure = WaltInput(modal.content, placeholder="Max Tenure (months)")
        max_tenure.pack(fill="x", pady=6)
        rate = WaltInput(modal.content, placeholder="Base Interest Rate")
        rate.pack(fill="x", pady=6)
        fee = WaltInput(modal.content, placeholder="Processing Fee %")
        fee.pack(fill="x", pady=6)

        def save_type() -> None:
            try:
                self.db.execute(
                    """
                    INSERT INTO loan_types (
                        name, min_amount, max_amount,
                        min_tenure_months, max_tenure_months,
                        base_interest_rate, processing_fee_percent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name.get(),
                        float(min_amount.get() or 0),
                        float(max_amount.get() or 0),
                        int(float(min_tenure.get() or 0)),
                        int(float(max_tenure.get() or 0)),
                        float(rate.get() or 0),
                        float(fee.get() or 0),
                    ),
                )
                modal.destroy()
                self._refresh_loan_types()
                self._toast("Loan type added", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        WaltButton(modal.footer, text="Cancel", style="secondary", command=modal.destroy).pack(side="right", padx=(8, 0))
        WaltButton(modal.footer, text="Save", style="primary", command=save_type).pack(side="right")

    def _build_users_tab(self) -> None:
        if not self._can_admin():
            tk.Label(self.users_tab, text="User management is restricted to admins.", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w", padx=14, pady=14)
            return

        container_card = WaltCard(self.users_tab, padding=14, radius=18, outer_bg=PALETTE.window_bg)
        container_card.pack(fill="both", expand=True, padx=14, pady=14)
        container = container_card.content

        WaltButton(container, text="Add Officer", style="primary", command=self._open_add_user_modal).pack(anchor="w")

        self.users_table = WaltTable(
            container,
            columns=[
                ("id", "ID", 50),
                ("full_name", "Name", 170),
                ("username", "Username", 120),
                ("email", "Email", 190),
                ("role", "Role", 90),
                ("is_active", "Active", 80),
            ],
        )
        self.users_table.pack(fill="both", expand=True, pady=(10, 0))

        self._refresh_users()

    def _refresh_users(self) -> None:
        if not hasattr(self, "users_table"):
            return
        rows = USER_MODEL.list_users()
        for row in rows:
            row["is_active"] = "Yes" if int(row.get("is_active", 0)) == 1 else "No"
        self.users_table.set_data(rows)

    def _open_add_user_modal(self) -> None:
        modal = WaltModal(self.winfo_toplevel(), "Add Officer", width=560, height=500)

        full_name = WaltInput(modal.content, placeholder="Full Name")
        full_name.pack(fill="x", pady=6)
        username = WaltInput(modal.content, placeholder="Username")
        username.pack(fill="x", pady=6)
        email = WaltInput(modal.content, placeholder="Email")
        email.pack(fill="x", pady=6)
        phone = WaltInput(modal.content, placeholder="Phone")
        phone.pack(fill="x", pady=6)
        password = WaltInput(modal.content, placeholder="Password", show_password_toggle=True, is_password=True)
        password.pack(fill="x", pady=6)

        role_var = tk.StringVar(value="officer")
        ttk.Combobox(modal.content, values=["admin", "officer", "viewer"], textvariable=role_var, state="readonly", style="Walt.TCombobox").pack(fill="x", pady=6)

        def save_user() -> None:
            try:
                USER_MODEL.create_officer(
                    {
                        "full_name": full_name.get(),
                        "username": username.get(),
                        "email": email.get(),
                        "phone": phone.get(),
                        "password": password.get(),
                        "confirm_password": password.get(),
                        "role": role_var.get(),
                    },
                    actor_user_id=self.current_user_id,
                )
                modal.destroy()
                self._refresh_users()
                self._toast("User created", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        WaltButton(modal.footer, text="Cancel", style="secondary", command=modal.destroy).pack(side="right", padx=(8, 0))
        WaltButton(modal.footer, text="Save", style="primary", command=save_user).pack(side="right")

    def _build_audit_tab(self) -> None:
        container_card = WaltCard(self.audit_tab, padding=14, radius=18, outer_bg=PALETTE.window_bg)
        container_card.pack(fill="both", expand=True, padx=14, pady=14)
        container = container_card.content

        filter_row = tk.Frame(container, bg=PALETTE.window_bg)
        filter_row.pack(fill="x")

        self.audit_search = WaltInput(filter_row, placeholder="Search module/action")
        self.audit_search.pack(side="left", fill="x", expand=True)
        WaltButton(filter_row, text="Search", style="secondary", command=self._refresh_audit).pack(side="left", padx=(8, 0))

        self.audit_table = WaltTable(
            container,
            columns=[
                ("timestamp", "Timestamp", 140),
                ("user_id", "User ID", 70),
                ("module", "Module", 100),
                ("action", "Action", 90),
                ("record_id", "Record", 70),
                ("ip_address", "IP", 100),
            ],
        )
        self.audit_table.pack(fill="both", expand=True, pady=(10, 0))

        self._refresh_audit()

    def _refresh_audit(self) -> None:
        query = self.audit_search.get().strip()
        if query:
            rows = self.db.fetchall(
                """
                SELECT timestamp, user_id, module, action, record_id, ip_address
                FROM audit_log
                WHERE module LIKE ? OR action LIKE ?
                ORDER BY timestamp DESC
                LIMIT 500
                """,
                (f"%{query}%", f"%{query}%"),
            )
        else:
            rows = self.db.fetchall(
                """
                SELECT timestamp, user_id, module, action, record_id, ip_address
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT 500
                """
            )
        self.audit_table.set_data([dict(row) for row in rows])

    def _build_database_tab(self) -> None:
        container_card = WaltCard(self.database_tab, padding=14, radius=18, outer_bg=PALETTE.window_bg)
        container_card.pack(fill="x", padx=14, pady=14)
        container = container_card.content

        db_path = Path(self.db.db_path)

        stats = self.db.fetchone(
            """
            SELECT
                (SELECT COUNT(*) FROM users) AS users_count,
                (SELECT COUNT(*) FROM customers) AS customers_count,
                (SELECT COUNT(*) FROM loans) AS loans_count,
                (SELECT COUNT(*) FROM repayments) AS repayments_count,
                (SELECT COUNT(*) FROM documents) AS documents_count
            """
        )

        tk.Label(container, text=f"Database File: {db_path}", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, wraplength=900, justify="left").pack(anchor="w")
        tk.Label(container, text=f"Users: {stats['users_count']} | Customers: {stats['customers_count']} | Loans: {stats['loans_count']} | Repayments: {stats['repayments_count']} | Documents: {stats['documents_count']}", bg=PALETTE.window_bg, fg=PALETTE.text_primary, pady=8).pack(anchor="w")

        actions = tk.Frame(container, bg=PALETTE.window_bg)
        actions.pack(fill="x", pady=(10, 0))

        WaltButton(actions, text="Backup Database", style="primary", command=self._backup_database).pack(side="left")
        WaltButton(actions, text="Restore Database", style="secondary", command=self._restore_database).pack(side="left", padx=(8, 0))

    def _backup_database(self) -> None:
        target = filedialog.asksaveasfilename(
            title="Save backup",
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")],
            initialfile="waltconsultant_backup.db",
        )
        if not target:
            return

        source = Path(self.db.db_path)
        try:
            shutil.copy2(source, target)
            self._toast("Database backup created", "success")
        except Exception as error:
            self._toast(str(error), "danger")

    def _restore_database(self) -> None:
        source = filedialog.askopenfilename(title="Select backup file", filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")])
        if not source:
            return

        def restore_now() -> None:
            target = Path(self.db.db_path)
            try:
                with sqlite3.connect(source) as src_conn, sqlite3.connect(target) as dst_conn:
                    src_conn.backup(dst_conn)
                self._toast("Database restored. Restart app to refresh in-memory views.", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        WaltConfirmDialog(self.winfo_toplevel(), "Restore Database", "Restoring will overwrite current data. Continue?", restore_now)
