"""Card component for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from utils.theme import PALETTE


class WaltCard(tk.Frame):
    def __init__(
        self,
        parent,
        padding: int = 20,
        radius: int = 16,
        border_color: str = PALETTE.divider,
        card_bg: str = PALETTE.window_bg,
        **kwargs,
    ):
        outer_bg = kwargs.pop("outer_bg", None)
        if outer_bg is None:
            try:
                outer_bg = str(parent.cget("bg"))
            except Exception:
                outer_bg = PALETTE.window_bg

        super().__init__(parent, bg=outer_bg, highlightthickness=0, bd=0, **kwargs)
        self.radius = radius
        self.border_color = border_color
        self.card_bg = card_bg

        self._canvas = tk.Canvas(self, bg=outer_bg, highlightthickness=0, bd=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.content = tk.Frame(self, bg=self.card_bg)
        self.content.pack(fill="both", expand=True, padx=padding, pady=padding)
        self._ensure_content_front()

        self.bind("<Configure>", self._draw_background)
        self.after(0, self._draw_background)

    def _ensure_content_front(self) -> None:
        try:
            self.tk.call("lower", self._canvas._w, self.content._w)
        except Exception:
            pass
        self.content.lift()

    def _draw_rounded_rect(self, x1: int, y1: int, x2: int, y2: int, radius: int) -> None:
        self._canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=self.card_bg, outline="", tags="card")
        self._canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=self.card_bg, outline="", tags="card")
        self._canvas.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, fill=self.card_bg, outline="", tags="card")
        self._canvas.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, fill=self.card_bg, outline="", tags="card")
        self._canvas.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, fill=self.card_bg, outline="", tags="card")
        self._canvas.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, fill=self.card_bg, outline="", tags="card")

        self._canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=self.border_color, width=1, tags="card")
        self._canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=self.border_color, width=1, tags="card")
        self._canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=self.border_color, width=1, tags="card")
        self._canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=self.border_color, width=1, tags="card")
        self._canvas.create_arc(x1, y1, x1 + radius * 2, y1 + radius * 2, start=90, extent=90, style="arc", outline=self.border_color, width=1, tags="card")
        self._canvas.create_arc(x2 - radius * 2, y1, x2, y1 + radius * 2, start=0, extent=90, style="arc", outline=self.border_color, width=1, tags="card")
        self._canvas.create_arc(x1, y2 - radius * 2, x1 + radius * 2, y2, start=180, extent=90, style="arc", outline=self.border_color, width=1, tags="card")
        self._canvas.create_arc(x2 - radius * 2, y2 - radius * 2, x2, y2, start=270, extent=90, style="arc", outline=self.border_color, width=1, tags="card")

    def _draw_background(self, _event=None) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 6 or height < 6:
            return

        radius = min(self.radius, (width - 2) // 2, (height - 2) // 2)
        self._canvas.delete("card")
        self._draw_rounded_rect(1, 1, width - 1, height - 1, radius)
        self._canvas.lower("card")
        self._ensure_content_front()
