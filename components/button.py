"""Custom button component for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from utils.theme import PALETTE


class WaltButton(tk.Button):
    STYLE_MAP = {
        "primary": {"bg": PALETTE.primary, "fg": "#FFFFFF", "activebackground": PALETTE.primary_hover},
        "secondary": {"bg": PALETTE.input_bg, "fg": PALETTE.text_primary, "activebackground": "#E9E9EF"},
        "destructive": {"bg": PALETTE.danger, "fg": "#FFFFFF", "activebackground": "#E63026"},
        "ghost": {"bg": PALETTE.window_bg, "fg": PALETTE.primary, "activebackground": "#EFF6FF"},
    }

    def __init__(self, parent, text: str, style: str = "primary", command=None, width: int | None = None, **kwargs):
        palette = self.STYLE_MAP.get(style, self.STYLE_MAP["primary"])
        super().__init__(
            parent,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            cursor="hand2",
            bg=palette["bg"],
            fg=palette["fg"],
            activebackground=palette["activebackground"],
            activeforeground=palette["fg"],
            padx=16,
            pady=8,
            font=("SF Pro Rounded", 11, "bold"),
            highlightthickness=0,
            **kwargs,
        )
        self.default_bg = palette["bg"]
        self.hover_bg = palette["activebackground"]

        if width:
            self.configure(width=width)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event):
        if self["state"] != "disabled":
            self.configure(bg=self.hover_bg)

    def _on_leave(self, _event):
        if self["state"] != "disabled":
            self.configure(bg=self.default_bg)
