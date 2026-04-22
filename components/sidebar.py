"""Sidebar navigation component for WaltConsultant."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from utils.constants import SIDEBAR_ITEMS
from utils.theme import PALETTE, SIZING


DISPLAY_NAME_MAP = {
    "Dashboard": "Overview",
    "Loans": "Assets",
    "Repayments": "Transactions",
    "Logout": "Sign Out",
}


class SidebarItem(tk.Canvas):
    def __init__(self, parent, name: str, on_click: Callable[[str], None]):
        super().__init__(
            parent,
            bg=PALETTE.sidebar_bg,
            height=48,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.name = name
        self.display_name = DISPLAY_NAME_MAP.get(name, name)
        self.on_click = on_click
        self.is_logout = name.lower() == "logout"
        self.is_selected = False
        self.is_hovered = False

        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._hover_enter)
        self.bind("<Leave>", self._hover_leave)
        self.bind("<Configure>", self._on_resize)
        self._redraw()

    def _on_resize(self, _event) -> None:
        self._redraw()

    def _create_rounded_rect(self, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs) -> None:
        self.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kwargs)
        self.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kwargs)
        self.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, **kwargs)
        self.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, **kwargs)
        self.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, **kwargs)
        self.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, **kwargs)

    def _state_colors(self) -> tuple[str, str]:
        if self.is_logout:
            return ("#FDECEE", "#D23340") if self.is_hovered else (PALETTE.sidebar_bg, "#D23340")

        if self.is_selected:
            return "#DCE9FB", "#147CE6"

        if self.is_hovered:
            return "#ECEFF4", "#59606D"

        return PALETTE.sidebar_bg, "#666C78"

    def _redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), SIZING.sidebar_width - 18)
        height = max(self.winfo_height(), 48)

        bg, fg = self._state_colors()
        top = 4
        bottom = height - 4
        left = 6
        right = width - 6

        if bg != PALETTE.sidebar_bg:
            radius = (bottom - top) // 2
            self._create_rounded_rect(left, top, right, bottom, radius, fill=bg, outline=bg)

        icon_x = 26
        icon_y = height // 2
        self._draw_icon(icon_x, icon_y, fg)

        font_weight = "bold" if self.is_selected or self.is_logout else "normal"
        self.create_text(
            52,
            icon_y,
            text=self.display_name,
            anchor="w",
            fill=fg,
            font=("SF Pro Rounded", 12, font_weight),
        )

    def _draw_icon(self, x: int, y: int, color: str) -> None:
        name = self.name.lower()
        if "dashboard" in name:
            self._draw_overview_icon(x, y, color)
        elif "customer" in name:
            self._draw_customers_icon(x, y, color)
        elif "loan" in name:
            self._draw_assets_icon(x, y, color)
        elif "repayment" in name:
            self._draw_transactions_icon(x, y, color)
        elif "report" in name:
            self._draw_reports_icon(x, y, color)
        elif "document" in name:
            self._draw_documents_icon(x, y, color)
        elif "setting" in name:
            self._draw_settings_icon(x, y, color)
        elif "logout" in name:
            self._draw_logout_icon(x, y, color)
        else:
            self.create_rectangle(x - 7, y - 6, x + 7, y + 6, outline=color, width=2)

    def _draw_overview_icon(self, x: int, y: int, color: str) -> None:
        left = x - 8
        top = y - 8
        cell = 6
        gap = 2
        for row in range(2):
            for col in range(2):
                cx = left + col * (cell + gap)
                cy = top + row * (cell + gap)
                self.create_rectangle(cx, cy, cx + cell, cy + cell, fill=color, outline=color)

    def _draw_customers_icon(self, x: int, y: int, color: str) -> None:
        self.create_oval(x - 9, y - 9, x - 3, y - 3, fill=color, outline=color)
        self.create_oval(x - 2, y - 10, x + 6, y - 2, fill=color, outline=color)
        self.create_arc(x - 13, y - 4, x - 1, y + 8, start=0, extent=180, style="pieslice", fill=color, outline=color)
        self.create_arc(x - 5, y - 5, x + 10, y + 9, start=0, extent=180, style="pieslice", fill=color, outline=color)

    def _draw_assets_icon(self, x: int, y: int, color: str) -> None:
        self.create_rectangle(x - 10, y - 7, x + 10, y + 8, outline=color, width=2)
        self.create_rectangle(x - 10, y - 2, x + 4, y + 8, outline=color, width=2)
        self.create_line(x - 8, y - 1, x + 7, y - 1, fill=color, width=2)
        self.create_oval(x + 4, y + 1, x + 7, y + 4, fill=color, outline=color)

    def _draw_transactions_icon(self, x: int, y: int, color: str) -> None:
        self.create_rectangle(x - 7, y - 9, x + 7, y + 9, outline=color, width=2)
        self.create_rectangle(x - 4, y - 12, x + 4, y - 9, fill=color, outline=color)
        self.create_line(x - 4, y - 3, x + 4, y - 3, fill=color, width=2)
        self.create_line(x - 4, y + 1, x + 4, y + 1, fill=color, width=2)
        self.create_line(x - 4, y + 5, x + 2, y + 5, fill=color, width=2)

    def _draw_reports_icon(self, x: int, y: int, color: str) -> None:
        self.create_line(x - 9, y + 8, x + 9, y + 8, fill=color, width=2)
        self.create_rectangle(x - 8, y + 1, x - 4, y + 8, fill=color, outline=color)
        self.create_rectangle(x - 1, y - 3, x + 3, y + 8, fill=color, outline=color)
        self.create_rectangle(x + 6, y - 7, x + 9, y + 8, fill=color, outline=color)

    def _draw_documents_icon(self, x: int, y: int, color: str) -> None:
        self.create_polygon(
            x - 6,
            y - 9,
            x + 1,
            y - 9,
            x + 6,
            y - 4,
            x + 6,
            y + 9,
            x - 6,
            y + 9,
            outline=color,
            fill="",
            width=2,
        )
        self.create_line(x + 1, y - 9, x + 1, y - 4, fill=color, width=2)
        self.create_line(x + 1, y - 4, x + 6, y - 4, fill=color, width=2)
        self.create_line(x - 3, y - 1, x + 3, y - 1, fill=color, width=2)
        self.create_line(x - 3, y + 3, x + 3, y + 3, fill=color, width=2)

    def _draw_settings_icon(self, x: int, y: int, color: str) -> None:
        self.create_oval(x - 5, y - 5, x + 5, y + 5, outline=color, width=2)
        self.create_oval(x - 2, y - 2, x + 2, y + 2, fill=color, outline=color)
        self.create_line(x, y - 9, x, y - 6, fill=color, width=2)
        self.create_line(x, y + 6, x, y + 9, fill=color, width=2)
        self.create_line(x - 9, y, x - 6, y, fill=color, width=2)
        self.create_line(x + 6, y, x + 9, y, fill=color, width=2)
        self.create_line(x - 7, y - 7, x - 5, y - 5, fill=color, width=2)
        self.create_line(x + 7, y + 7, x + 5, y + 5, fill=color, width=2)
        self.create_line(x - 7, y + 7, x - 5, y + 5, fill=color, width=2)
        self.create_line(x + 7, y - 7, x + 5, y - 5, fill=color, width=2)

    def _draw_logout_icon(self, x: int, y: int, color: str) -> None:
        self.create_rectangle(x - 1, y - 8, x + 8, y + 8, outline=color, width=2)
        self.create_line(x - 10, y, x + 2, y, fill=color, width=2, capstyle="round")
        self.create_line(x - 6, y - 4, x - 10, y, fill=color, width=2, capstyle="round")
        self.create_line(x - 6, y + 4, x - 10, y, fill=color, width=2, capstyle="round")

    def set_selected(self, selected: bool) -> None:
        self.is_selected = bool(selected and not self.is_logout)
        self._redraw()

    def _click(self, _event):
        self.on_click(self.name)

    def _hover_enter(self, _event):
        self.is_hovered = True
        self._redraw()

    def _hover_leave(self, _event):
        self.is_hovered = False
        self._redraw()


class WaltSidebar(tk.Frame):
    def __init__(self, parent, on_navigate: Callable[[str], None]):
        super().__init__(parent, bg=PALETTE.sidebar_bg, width=SIZING.sidebar_width)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.items: dict[str, SidebarItem] = {}

        container = tk.Frame(self, bg=PALETTE.sidebar_bg)
        container.pack(fill="both", expand=True, padx=10, pady=12)

        top_group = tk.Frame(container, bg=PALETTE.sidebar_bg)
        top_group.pack(fill="x", side="top")

        for item_name in SIDEBAR_ITEMS[:-1]:
            item = SidebarItem(top_group, item_name, self._handle_click)
            item.pack(fill="x", pady=3)
            self.items[item_name] = item

        bottom_group = tk.Frame(container, bg=PALETTE.sidebar_bg)
        bottom_group.pack(fill="x", side="bottom")

        logout_item = SidebarItem(bottom_group, SIDEBAR_ITEMS[-1], self._handle_click)
        logout_item.pack(fill="x", pady=3)
        self.items[SIDEBAR_ITEMS[-1]] = logout_item

        self.set_selected("Dashboard")

    def _handle_click(self, name: str) -> None:
        self.set_selected(name)
        self.on_navigate(name)

    def set_selected(self, name: str) -> None:
        for item_name, item in self.items.items():
            item.set_selected(item_name == name)
