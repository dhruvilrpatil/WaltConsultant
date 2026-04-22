"""Input components for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from components.card import WaltCard
from utils.theme import PALETTE


class WaltInput(tk.Frame):
    def __init__(
        self,
        parent,
        placeholder: str = "",
        icon: str = "",
        show_password_toggle: bool = False,
        width: int = 32,
        is_password: bool = False,
    ):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.placeholder = placeholder
        self.show_password_toggle = show_password_toggle or is_password
        self.is_password = is_password
        self.placeholder_visible = False
        self._error_visible = False

        wrapper = WaltCard(
            self,
            padding=0,
            radius=10,
            border_color=PALETTE.divider,
            card_bg=PALETTE.input_bg,
            outer_bg=PALETTE.window_bg,
        )
        wrapper.pack(fill="x")
        wrapper_content = wrapper.content

        if icon:
            self.icon_label = tk.Label(wrapper_content, text=icon, bg=PALETTE.input_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 11))
            self.icon_label.pack(side="left", padx=(10, 4), pady=8)

        self.var = tk.StringVar()
        self.entry = tk.Entry(
            wrapper_content,
            textvariable=self.var,
            bd=0,
            relief="flat",
            bg=PALETTE.input_bg,
            fg=PALETTE.text_primary,
            width=width,
            font=("SF Pro Rounded", 12),
            insertbackground=PALETTE.text_primary,
            show="*" if is_password else "",
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 8), pady=8)

        self.toggle_btn: tk.Button | None = None
        if self.show_password_toggle:
            self.toggle_btn = tk.Button(
                wrapper_content,
                text="Show",
                bd=0,
                relief="flat",
                bg=PALETTE.input_bg,
                fg=PALETTE.primary,
                cursor="hand2",
                font=("SF Pro Rounded", 10),
                command=self.toggle_password,
            )
            self.toggle_btn.pack(side="right", padx=(0, 8), pady=6)

        self.error_label = tk.Label(self, text="", bg=PALETTE.window_bg, fg=PALETTE.danger, anchor="w", font=("SF Pro Rounded", 10))

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

        if placeholder:
            self._show_placeholder()

    def _show_placeholder(self) -> None:
        if self.var.get():
            return
        self.placeholder_visible = True
        self.entry.delete(0, "end")
        self.entry.insert(0, self.placeholder)
        self.entry.configure(fg=PALETTE.text_tertiary, show="")

    def _clear_placeholder(self) -> None:
        if not self.placeholder_visible:
            return
        self.placeholder_visible = False
        self.entry.delete(0, "end")
        self.entry.configure(fg=PALETTE.text_primary)
        if self.is_password and not self._is_password_visible():
            self.entry.configure(show="*")

    def _on_focus_in(self, _event) -> None:
        self._clear_placeholder()

    def _on_focus_out(self, _event) -> None:
        if not self.var.get().strip():
            self._show_placeholder()

    def _is_password_visible(self) -> bool:
        return self.entry.cget("show") == ""

    def toggle_password(self) -> None:
        if self.placeholder_visible:
            return
        if self._is_password_visible():
            self.entry.configure(show="*")
            if self.toggle_btn:
                self.toggle_btn.configure(text="Show")
        else:
            self.entry.configure(show="")
            if self.toggle_btn:
                self.toggle_btn.configure(text="Hide")

    def get(self) -> str:
        if self.placeholder_visible:
            return ""
        return self.var.get().strip()

    def set(self, value: str) -> None:
        self._clear_placeholder()
        self.var.set(value)

    def set_error(self, message: str) -> None:
        if not message:
            self.clear_error()
            return
        self.error_label.configure(text=message)
        if not self._error_visible:
            self.error_label.pack(fill="x", pady=(4, 0))
            self._error_visible = True

    def clear_error(self) -> None:
        self.error_label.configure(text="")
        if self._error_visible:
            self.error_label.pack_forget()
            self._error_visible = False


class WaltSearchBar(WaltInput):
    def __init__(self, parent, on_search=None, placeholder: str = "Search"):
        super().__init__(parent, placeholder=placeholder, icon="S")
        self.on_search = on_search
        self.entry.bind("<KeyRelease>", self._trigger_search)

    def _trigger_search(self, _event) -> None:
        if self.on_search:
            self.on_search(self.get())
