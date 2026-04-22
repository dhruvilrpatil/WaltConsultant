"""Splash screen for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from components.progress import WaltProgressBar
from utils.constants import APP_NAME, APP_TAGLINE
from utils.theme import PALETTE


class SplashScreen(tk.Frame):
    def __init__(self, parent, on_complete):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.on_complete = on_complete
        self.progress = 0

        center = tk.Frame(self, bg=PALETTE.window_bg)
        center.place(relx=0.5, rely=0.5, anchor="center")

        logo = tk.Canvas(center, width=84, height=84, bg=PALETTE.window_bg, highlightthickness=0)
        logo.pack(pady=(0, 20))
        logo.create_rectangle(10, 10, 74, 74, fill=PALETTE.primary, outline=PALETTE.primary)
        logo.create_text(42, 42, text="W", fill="#FFFFFF", font=("SF Pro Rounded", 30, "bold"))

        tk.Label(center, text=APP_NAME, bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 28, "bold")).pack()
        tk.Label(center, text=APP_TAGLINE, bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 14)).pack(pady=(8, 0))

        self.progress_bar = WaltProgressBar(self, value=0, max_value=100, color=PALETTE.primary, width=460, height=4)
        self.progress_bar.pack(side="bottom", pady=20)

        self.after(30, self._tick)

    def _tick(self) -> None:
        self.progress += 1.7
        self.progress_bar.set_value(self.progress)
        if self.progress >= 100:
            self.after(120, self.on_complete)
            return
        self.after(30, self._tick)
