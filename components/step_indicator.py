"""Step indicator component for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from utils.theme import PALETTE


class WaltStepIndicator(tk.Frame):
    def __init__(self, parent, steps: list[str], current: int = 1):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.steps = steps
        self.current = current
        self._render()

    def _render(self) -> None:
        for child in self.winfo_children():
            child.destroy()

        for index, step in enumerate(self.steps, start=1):
            color = PALETTE.primary if index <= self.current else PALETTE.divider
            text_color = "#FFFFFF" if index <= self.current else PALETTE.text_secondary

            bubble = tk.Canvas(self, width=24, height=24, bg=PALETTE.window_bg, highlightthickness=0)
            bubble.pack(side="left")
            bubble.create_oval(2, 2, 22, 22, fill=color, outline=color)
            bubble.create_text(12, 12, text=str(index), fill=text_color, font=("SF Pro Rounded", 9, "bold"))

            tk.Label(self, text=step, bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 10)).pack(side="left", padx=(6, 12))

            if index < len(self.steps):
                line_color = PALETTE.primary if index < self.current else PALETTE.divider
                tk.Frame(self, bg=line_color, width=28, height=2).pack(side="left", padx=(0, 12), pady=11)

    def set_current(self, current: int) -> None:
        self.current = max(1, min(len(self.steps), current))
        self._render()
