"""Badge component for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from utils.theme import PALETTE


BADGE_COLORS = {
    "green": ("#E9F9EF", PALETTE.success),
    "blue": ("#EAF2FF", PALETTE.primary),
    "red": ("#FFE9E7", PALETTE.danger),
    "amber": ("#FFF4E6", PALETTE.warning),
    "gray": ("#F0F1F4", PALETTE.text_secondary),
}


class WaltBadge(tk.Label):
    def __init__(self, parent, text: str, color: str = "blue", **kwargs):
        bg, fg = BADGE_COLORS.get(color, BADGE_COLORS["blue"])
        super().__init__(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            font=("SF Pro Rounded", 10, "bold"),
            padx=10,
            pady=2,
            **kwargs,
        )
