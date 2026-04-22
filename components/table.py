"""Table component for WaltConsultant."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from utils.theme import PALETTE, is_dark_mode, setup_ttk_styles


class WaltTable(tk.Frame):
    def __init__(self, parent, columns: list[tuple[str, str, int]], data: list[dict[str, Any]] | None = None, on_row_click: Callable[[dict[str, Any]], None] | None = None):
        super().__init__(parent, bg=PALETTE.window_bg)
        setup_ttk_styles(self.winfo_toplevel())
        dark_mode = is_dark_mode()

        self.columns = columns
        self.on_row_click = on_row_click
        self._rows_cache: list[dict[str, Any]] = []
        self._row_bg = "#151C2A" if dark_mode else PALETTE.window_bg
        self._row_alt_bg = "#1A2334" if dark_mode else "#FAFBFD"

        self.tree = ttk.Treeview(self, columns=[col[0] for col in columns], show="headings", style="Walt.Treeview")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.tag_configure("odd", background=self._row_bg, foreground=PALETTE.text_primary)
        self.tree.tag_configure("even", background=self._row_alt_bg, foreground=PALETTE.text_primary)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview, style="Walt.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        for field, title, width in columns:
            self.tree.heading(field, text=title, command=lambda f=field: self._sort_by(f, False))
            self.tree.column(field, width=width, anchor="w")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        if data:
            self.set_data(data)

    def set_data(self, data: list[dict[str, Any]]) -> None:
        self._rows_cache = data
        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, row in enumerate(data):
            values = [row.get(field, "") for field, _, _ in self.columns]
            tag = "even" if index % 2 == 0 else "odd"
            self.tree.insert("", "end", values=values, tags=(tag,))

    def _on_select(self, _event) -> None:
        if not self.on_row_click:
            return
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = item.get("values", [])
        row = {}
        for index, (field, _, _) in enumerate(self.columns):
            row[field] = values[index] if index < len(values) else None
        self.on_row_click(row)

    def _sort_by(self, field: str, descending: bool) -> None:
        children = [(self.tree.set(child, field), child) for child in self.tree.get_children("")]
        children.sort(reverse=descending)

        for index, (_value, child) in enumerate(children):
            self.tree.move(child, "", index)

        self.tree.heading(field, command=lambda: self._sort_by(field, not descending))
