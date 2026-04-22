"""Progress bar component for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from utils.theme import PALETTE


class WaltProgressBar(tk.Frame):
    def __init__(self, parent, value: float = 0, max_value: float = 100, color: str = PALETTE.primary, width: int = 280, height: int = 6):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.max_value = max_value
        self.color = color
        self.width = width
        self.height = height

        self.canvas = tk.Canvas(self, width=width, height=height, bg=PALETTE.window_bg, highlightthickness=0)
        self.canvas.pack(fill="x", expand=True)
        self.track = self.canvas.create_rectangle(0, 0, width, height, fill=PALETTE.input_bg, outline=PALETTE.input_bg)
        self.bar = self.canvas.create_rectangle(0, 0, 0, height, fill=self.color, outline=self.color)
        self.set_value(value)

    def set_value(self, value: float) -> None:
        progress = 0 if self.max_value <= 0 else max(0, min(1, value / self.max_value))
        self.canvas.coords(self.bar, 0, 0, self.width * progress, self.height)
