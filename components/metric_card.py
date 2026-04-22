"""Metric card component for WaltConsultant dashboard."""

from __future__ import annotations

import tkinter as tk

from components.card import WaltCard
from utils.theme import PALETTE


class WaltMetricCard(WaltCard):
    def __init__(self, parent, title: str, value: str, subtitle: str = "", icon: str = "", trend: str = ""):
        super().__init__(parent, padding=16)

        top = tk.Frame(self.content, bg=PALETTE.window_bg)
        top.pack(fill="x")

        tk.Label(top, text=title, bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 11)).pack(side="left")
        if icon:
            tk.Label(top, text=icon, bg=PALETTE.window_bg, fg=PALETTE.primary, font=("SF Pro Rounded", 12, "bold")).pack(side="right")

        self.value_label = tk.Label(self.content, text=value, bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 18, "bold"))
        self.value_label.pack(anchor="w", pady=(8, 2))

        self.subtitle_label = tk.Label(self.content, text=subtitle, bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 10))
        self.subtitle_label.pack(anchor="w")

        if trend:
            tk.Label(self.content, text=trend, bg=PALETTE.window_bg, fg=PALETTE.success, font=("SF Pro Rounded", 10, "bold")).pack(anchor="w", pady=(6, 0))

    def update_values(self, value: str, subtitle: str = "") -> None:
        self.value_label.configure(text=value)
        self.subtitle_label.configure(text=subtitle)
