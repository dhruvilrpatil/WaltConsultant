"""Signup screen for WaltConsultant with executive split-panel styling."""

from __future__ import annotations

import re
import tkinter as tk
from datetime import datetime

from components.card import WaltCard
from utils.constants import APP_NAME
from utils.validators import validate_signup_fields


class SignupScreen(tk.Frame):
    def __init__(self, parent, on_create_account, on_show_login):
        super().__init__(parent, bg="#E8EBEF")
        self.on_create_account = on_create_account
        self.on_show_login = on_show_login

        self.full_name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.accept_terms_var = tk.BooleanVar(value=False)
        self.password_visible = False

        self._build_layout()

    def _build_layout(self) -> None:
        shell = tk.Frame(self, bg="#DDE2E8")
        shell.pack(fill="both", expand=True, padx=28, pady=28)

        self.card = WaltCard(shell, padding=0, radius=20, border_color="#D4D8DE", card_bg="#F3F4F6", outer_bg="#DDE2E8")
        self.card.pack(fill="both", expand=True)

        left = tk.Frame(self.card.content, bg="#031222", width=500)
        left.pack(side="left", fill="both")
        left.pack_propagate(False)

        right = tk.Frame(self.card.content, bg="#F3F4F6", width=460)
        right.pack(side="left", fill="both", expand=True)
        right.pack_propagate(False)

        self._build_left_panel(left)
        self._build_right_panel(right)

        footer = tk.Frame(self, bg="#E8EBEF")
        footer.pack(fill="x", padx=36, pady=(0, 14))
        tk.Label(footer, text=f"© 2026 {APP_NAME}. Architectural precision in strategy.", bg="#E8EBEF", fg="#667284", font=("SF Pro Rounded", 10)).pack(side="left")

    def _build_left_panel(self, parent: tk.Frame) -> None:
        canvas = tk.Canvas(parent, bg="#031222", highlightthickness=0)
        canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        for i in range(16):
            y = 180 + (i * 26)
            canvas.create_line(0, y, 520, y - 220, fill="#0E2E49", width=1)

        content = tk.Frame(parent, bg="#031222")
        content.pack(fill="both", expand=True, padx=30, pady=28)

        tk.Label(content, text=APP_NAME, bg="#031222", fg="#FFFFFF", font=("SF Pro Rounded", 22, "bold"), padx=4).pack(anchor="w", pady=(0, 40))

        tk.Label(
            content,
            text="Architectural\nprecision\nin strategy.",
            justify="left",
            bg="#031222",
            fg="#FFFFFF",
            font=("SF Pro Rounded", 42, "bold"),
            wraplength=420,
            padx=4,
        ).pack(anchor="w")

        tk.Label(
            content,
            text="Join an elite network of consultants defining the next\nera of industrial and corporate excellence through\nmeticulous planning and data-driven insights.",
            justify="left",
            bg="#031222",
            fg="#8BA0B6",
            font=("SF Pro Rounded", 12),
            wraplength=420,
        ).pack(anchor="w", pady=(22, 36))

        self._feature(content, "Structural Integrity", "Every recommendation is built on a foundation of verifiable\ntruth.")
        self._feature(content, "Global Insights", "Access the collective wisdom of over 500 senior lead\npartners.")

    def _feature(self, parent: tk.Widget, title: str, description: str) -> None:
        row = tk.Frame(parent, bg="#031222")
        row.pack(anchor="w", pady=(0, 16))

        icon = tk.Canvas(row, width=16, height=16, bg="#031222", highlightthickness=0)
        icon.pack(side="left", padx=(0, 10), pady=(1, 0))
        icon.create_line(3, 13, 8, 3, fill="#00A4FF", width=1)
        icon.create_line(8, 3, 13, 13, fill="#00A4FF", width=1)
        icon.create_oval(6, 1, 10, 5, outline="#00A4FF", width=1)

        text = tk.Frame(row, bg="#031222")
        text.pack(side="left")
        tk.Label(text, text=title, bg="#031222", fg="#F7FAFF", font=("SF Pro Rounded", 13, "bold")).pack(anchor="w")
        tk.Label(text, text=description, justify="left", bg="#031222", fg="#8EA3B8", font=("SF Pro Rounded", 10), wraplength=370).pack(anchor="w", pady=(3, 0))

    def _build_right_panel(self, parent: tk.Frame) -> None:
        body = tk.Frame(parent, bg="#F3F4F6")
        body.pack(fill="both", expand=True, padx=62, pady=80)

        tk.Label(body, text="Create Account", bg="#F3F4F6", fg="#171B23", font=("SF Pro Rounded", 38, "bold")).pack(anchor="w")
        tk.Label(body, text=f"Begin your partnership with {APP_NAME}.", bg="#F3F4F6", fg="#576273", font=("SF Pro Rounded", 12)).pack(anchor="w", pady=(8, 26))

        tk.Label(body, text="FULL NAME", bg="#F3F4F6", fg="#5B6472", font=("SF Pro Rounded", 10, "bold")).pack(anchor="w")
        self.full_name_entry = self._entry_block(body, self.full_name_var)

        tk.Label(body, text="PROFESSIONAL EMAIL", bg="#F3F4F6", fg="#5B6472", font=("SF Pro Rounded", 10, "bold")).pack(anchor="w", pady=(14, 0))
        self.email_entry = self._entry_block(body, self.email_var)

        tk.Label(body, text="PASSWORD", bg="#F3F4F6", fg="#5B6472", font=("SF Pro Rounded", 10, "bold")).pack(anchor="w", pady=(14, 0))
        password_wrap = WaltCard(body, padding=0, radius=10, border_color="#E0E3E8", card_bg="#E7E9ED", outer_bg="#F3F4F6")
        password_wrap.pack(fill="x", pady=(6, 0))

        self.password_entry = tk.Entry(
            password_wrap.content,
            textvariable=self.password_var,
            show="*",
            bg="#E7E9ED",
            fg="#111827",
            relief="flat",
            insertbackground="#111827",
            font=("SF Pro Rounded", 12),
            bd=0,
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(12, 6), pady=10)

        self.toggle_button = tk.Button(
            password_wrap.content,
            text="Show",
            command=self._toggle_password,
            bg="#E7E9ED",
            fg="#1D8FE3",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("SF Pro Rounded", 10, "bold"),
            padx=10,
        )
        self.toggle_button.pack(side="right", pady=8)

        terms = tk.Checkbutton(
            body,
            text="I agree to the account agreement.",
            variable=self.accept_terms_var,
            onvalue=True,
            offvalue=False,
            bg="#F3F4F6",
            fg="#5D6675",
            activebackground="#F3F4F6",
            activeforeground="#5D6675",
            selectcolor="#F3F4F6",
            highlightthickness=0,
            font=("SF Pro Rounded", 11),
            wraplength=420,
            justify="left",
        )
        terms.pack(anchor="w", pady=(16, 10))

        self.error_label = tk.Label(body, text="", bg="#F3F4F6", fg="#DC2626", font=("SF Pro Rounded", 10), justify="left", wraplength=420)
        self.error_label.pack(anchor="w", pady=(0, 8))

        create_button = tk.Button(
            body,
            text="Create Account",
            command=self._handle_signup,
            bg="#05080E",
            fg="#FFFFFF",
            activebackground="#101A2A",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("SF Pro Rounded", 12, "bold"),
            pady=13,
        )
        create_button.pack(fill="x")

        divider = tk.Frame(body, bg="#F3F4F6")
        divider.pack(fill="x", pady=18)
        tk.Frame(divider, bg="#E1E4E8", height=1).pack(fill="x")

        switch_row = tk.Frame(body, bg="#F3F4F6")
        switch_row.pack(fill="x")
        tk.Label(switch_row, text="Already have an account?", bg="#F3F4F6", fg="#596273", font=("SF Pro Rounded", 11)).pack(side="left")
        login_link = tk.Label(switch_row, text="Client Portal", bg="#F3F4F6", fg="#111827", font=("SF Pro Rounded", 11, "bold"), cursor="hand2")
        login_link.pack(side="left", padx=(8, 0))
        login_link.bind("<Button-1>", lambda _event: self.on_show_login())

        self.full_name_entry.bind("<Return>", lambda _event: self._handle_signup())
        self.email_entry.bind("<Return>", lambda _event: self._handle_signup())
        self.password_entry.bind("<Return>", lambda _event: self._handle_signup())

    def _entry_block(self, parent: tk.Widget, variable: tk.StringVar) -> tk.Entry:
        wrap = WaltCard(parent, padding=0, radius=10, border_color="#E0E3E8", card_bg="#E7E9ED", outer_bg="#F3F4F6")
        wrap.pack(fill="x", pady=(6, 0))
        entry = tk.Entry(
            wrap.content,
            textvariable=variable,
            bg="#E7E9ED",
            fg="#111827",
            relief="flat",
            insertbackground="#111827",
            font=("SF Pro Rounded", 12),
            bd=0,
        )
        entry.pack(fill="x", padx=12, pady=10)
        return entry

    def _toggle_password(self) -> None:
        self.password_visible = not self.password_visible
        self.password_entry.configure(show="" if self.password_visible else "*")
        self.toggle_button.configure(text="Hide" if self.password_visible else "Show")

    def _build_payload(self) -> dict[str, str]:
        email = self.email_var.get().strip().lower()
        full_name = self.full_name_var.get().strip()
        password = self.password_var.get()

        local_part = email.split("@", 1)[0] if "@" in email else ""
        base = re.sub(r"[^a-zA-Z0-9_.-]", "", local_part) or "user"
        suffix = datetime.utcnow().strftime("%H%M")
        username = f"{base[:24]}{suffix}"[:30]

        return {
            "full_name": full_name,
            "email": email,
            "username": username,
            "password": password,
            "confirm_password": password,
            "role": "officer",
            "country": "India",
        }

    def _handle_signup(self) -> None:
        self.error_label.configure(text="")

        if not self.accept_terms_var.get():
            self.show_error("Please accept the account agreement to continue.")
            return

        payload = self._build_payload()
        errors = validate_signup_fields(payload)
        if errors:
            self.show_error("; ".join(errors.values()))
            return

        self.on_create_account(payload)

    def show_error(self, message: str) -> None:
        self.error_label.configure(text=message)
        self._shake_card()

    def _shake_card(self) -> None:
        offsets = [-12, 8, -6, 4, -2, 0]
        self._animate_offsets(offsets, 0)

    def _animate_offsets(self, offsets: list[int], index: int) -> None:
        if index >= len(offsets):
            self.card.pack_configure(padx=0)
            return

        self.card.pack_configure(padx=offsets[index])
        self.after(24, lambda: self._animate_offsets(offsets, index + 1))
