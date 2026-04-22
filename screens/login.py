"""Login screen for WaltConsultant with executive split-panel styling."""

from __future__ import annotations

import tkinter as tk

from components.card import WaltCard
from utils.constants import APP_NAME


class LoginScreen(tk.Frame):
    def __init__(self, parent, on_login, on_show_signup):
        super().__init__(parent, bg="#E8EBEF")
        self.on_login = on_login
        self.on_show_signup = on_show_signup

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=False)
        self.password_visible = False

        self._build_layout()

    def _build_layout(self) -> None:
        shell = tk.Frame(self, bg="#DDE2E8")
        shell.pack(fill="both", expand=True, padx=28, pady=28)

        self.card = WaltCard(shell, padding=0, radius=20, border_color="#D4D8DE", card_bg="#F3F4F6", outer_bg="#DDE2E8")
        self.card.pack(fill="both", expand=True)

        left = tk.Frame(self.card.content, bg="#020812", width=500)
        left.pack(side="left", fill="both")
        left.pack_propagate(False)

        right = tk.Frame(self.card.content, bg="#F3F4F6", width=460)
        right.pack(side="left", fill="both", expand=True)
        right.pack_propagate(False)

        self._build_left_panel(left)
        self._build_right_panel(right)

        footer = tk.Frame(self, bg="#E8EBEF")
        footer.pack(fill="x", padx=36, pady=(0, 14))
        tk.Label(footer, text=f"© 2026 {APP_NAME}. Loan Management Solutions.", bg="#E8EBEF", fg="#667284", font=("SF Pro Rounded", 10)).pack(side="left")

    def _build_left_panel(self, parent: tk.Frame) -> None:
        canvas = tk.Canvas(parent, bg="#020812", highlightthickness=0)
        canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Subtle structural lines to emulate the visual texture in the reference.
        for i in range(12):
            x0 = 60 + (i * 40)
            canvas.create_line(x0, 520, x0 + 180, 130, fill="#0A223D", width=1)

        content = tk.Frame(parent, bg="#020812")
        content.pack(fill="both", expand=True, padx=36, pady=34)

        tk.Label(content, text=APP_NAME, bg="#020812", fg="#FFFFFF", font=("SF Pro Rounded", 31, "bold"), padx=4).pack(anchor="w")
        tk.Label(
            content,
            text="Architectural precision in corporate\nstrategy and operational excellence.",
            justify="left",
            bg="#020812",
            fg="#8096AF",
            font=("SF Pro Rounded", 14),
            wraplength=410,
        ).pack(anchor="w", pady=(16, 34))

        self._feature_item(content, "Strategic Insights", "Deep-dive analysis of market trends and\norganizational efficiency.")
        self._feature_item(content, "Structural Design", "Building resilient systems that scale with your\nglobal ambition.")

        tk.Frame(content, bg="#163455", height=1).pack(fill="x", pady=(28, 28))

        bottom = tk.Frame(content, bg="#020812")
        bottom.pack(fill="x", side="bottom")
        tk.Label(bottom, text="W", bg="#020812", fg="#1C2734", font=("SF Pro Rounded", 72, "bold")).pack(side="left")
        tk.Label(bottom, text="ESTABLISHED 2026", bg="#020812", fg="#6E8298", font=("SF Pro Rounded", 10)).pack(side="right", pady=(60, 0))

    def _feature_item(self, parent: tk.Widget, title: str, description: str) -> None:
        row = tk.Frame(parent, bg="#020812")
        row.pack(anchor="w", pady=(0, 20))

        icon = tk.Canvas(row, width=18, height=18, bg="#020812", highlightthickness=0)
        icon.pack(side="left", padx=(0, 12), pady=(2, 0))
        icon.create_rectangle(3, 3, 15, 15, outline="#00A3FF", width=1)
        icon.create_line(6, 10, 8, 7, fill="#00A3FF", width=1)
        icon.create_line(8, 7, 11, 11, fill="#00A3FF", width=1)
        icon.create_line(11, 11, 13, 5, fill="#00A3FF", width=1)

        text_col = tk.Frame(row, bg="#020812")
        text_col.pack(side="left")
        tk.Label(text_col, text=title, bg="#020812", fg="#F6F8FC", font=("SF Pro Rounded", 15, "bold")).pack(anchor="w")
        tk.Label(text_col, text=description, justify="left", bg="#020812", fg="#91A7BE", font=("SF Pro Rounded", 11), wraplength=380).pack(anchor="w", pady=(4, 0))

    def _build_right_panel(self, parent: tk.Frame) -> None:
        body = tk.Frame(parent, bg="#F3F4F6")
        body.pack(fill="both", expand=True, padx=58, pady=62)

        tk.Label(body, text="Welcome Back", bg="#F3F4F6", fg="#171B23", font=("SF Pro Rounded", 36, "bold")).pack(anchor="w")
        tk.Label(body, text="Access your executive dashboard and insights.", bg="#F3F4F6", fg="#576273", font=("SF Pro Rounded", 12)).pack(anchor="w", pady=(6, 24))

        tk.Label(body, text="USERNAME", bg="#F3F4F6", fg="#5B6472", font=("SF Pro Rounded", 10, "bold")).pack(anchor="w")
        self.username_entry = self._entry_block(body, self.username_var)

        pass_row = tk.Frame(body, bg="#F3F4F6")
        pass_row.pack(fill="x", pady=(12, 0))
        tk.Label(pass_row, text="PASSWORD", bg="#F3F4F6", fg="#5B6472", font=("SF Pro Rounded", 10, "bold")).pack(side="left")
        tk.Label(pass_row, text="Forgot Password?", bg="#F3F4F6", fg="#147CE6", cursor="hand2", font=("SF Pro Rounded", 10, "bold")).pack(side="right")

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

        remember = tk.Checkbutton(
            body,
            text="Keep me authenticated for 30 days",
            variable=self.remember_var,
            onvalue=True,
            offvalue=False,
            bg="#F3F4F6",
            fg="#5D6675",
            activebackground="#F3F4F6",
            activeforeground="#5D6675",
            highlightthickness=0,
            font=("SF Pro Rounded", 11),
            selectcolor="#F3F4F6",
        )
        remember.pack(anchor="w", pady=(16, 16))

        self.error_label = tk.Label(body, text="", bg="#F3F4F6", fg="#DC2626", font=("SF Pro Rounded", 10), justify="left")
        self.error_label.pack(anchor="w", pady=(0, 8))

        sign_button = tk.Button(
            body,
            text="Sign In to Portal",
            command=self._handle_login,
            bg="#0A1220",
            fg="#FFFFFF",
            activebackground="#111F34",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("SF Pro Rounded", 12, "bold"),
            pady=12,
        )
        sign_button.pack(fill="x")

        divider = tk.Frame(body, bg="#F3F4F6")
        divider.pack(fill="x", pady=18)
        tk.Frame(divider, bg="#E1E4E8", height=1).pack(side="left", fill="x", expand=True, pady=8)
        tk.Label(divider, text="PARTNERSHIP", bg="#F3F4F6", fg="#ADB4BE", font=("SF Pro Rounded", 9, "bold"), padx=12).pack(side="left")
        tk.Frame(divider, bg="#E1E4E8", height=1).pack(side="left", fill="x", expand=True, pady=8)

        tk.Label(body, text="New to our consultancy services?", bg="#F3F4F6", fg="#596273", font=("SF Pro Rounded", 11)).pack(pady=(2, 10))

        request_button = tk.Button(
            body,
            text="Request Client Access",
            command=self.on_show_signup,
            bg="#F3F4F6",
            fg="#1F2937",
            activebackground="#EBEEF2",
            activeforeground="#111827",
            relief="solid",
            bd=1,
            highlightthickness=0,
            cursor="hand2",
            font=("SF Pro Rounded", 10, "bold"),
            pady=10,
        )
        request_button.pack(fill="x")

        self.username_entry.bind("<Return>", lambda _event: self._handle_login())
        self.password_entry.bind("<Return>", lambda _event: self._handle_login())

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

    def _handle_login(self) -> None:
        self.clear_error()
        self.on_login(self.username_var.get().strip(), self.password_var.get())

    def show_error(self, message: str) -> None:
        self.error_label.configure(text=message)
        self._shake_card()

    def clear_error(self) -> None:
        self.error_label.configure(text="")

    def _shake_card(self) -> None:
        offsets = [-14, 10, -8, 5, -3, 0]
        self._animate_offsets(offsets, 0)

    def _animate_offsets(self, offsets: list[int], index: int) -> None:
        if index >= len(offsets):
            self.card.pack_configure(padx=0)
            return

        self.card.pack_configure(padx=offsets[index])
        self.after(26, lambda: self._animate_offsets(offsets, index + 1))
