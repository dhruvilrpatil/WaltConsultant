"""Modal components for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from components.button import WaltButton
from utils.theme import PALETTE


class WaltModal(tk.Toplevel):
    def __init__(self, parent, title: str, width: int = 640, height: int = 480):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=PALETTE.window_bg)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.width = width
        self.height = height
        self._center(parent)

        header = tk.Frame(self, bg=PALETTE.window_bg)
        header.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(header, text=title, bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 15, "bold")).pack(side="left")

        self.footer = tk.Frame(self, bg=PALETTE.window_bg)
        self.footer.pack(side="bottom", fill="x", padx=20, pady=(4, 16))

        self.content = tk.Frame(self, bg=PALETTE.window_bg)
        self.content.pack(fill="both", expand=True, padx=20, pady=12)

    def _center(self, parent) -> None:
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - self.width) // 2
        y = parent_y + (parent_h - self.height) // 2
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")


class WaltConfirmDialog(WaltModal):
    def __init__(self, parent, title: str, message: str, on_confirm):
        super().__init__(parent, title=title, width=440, height=220)

        tk.Label(self.content, text=message, bg=PALETTE.window_bg, fg=PALETTE.text_secondary, justify="left", wraplength=380, font=("SF Pro Rounded", 12)).pack(anchor="w")

        cancel_btn = WaltButton(self.footer, text="Cancel", style="secondary", command=self.destroy)
        cancel_btn.pack(side="right", padx=(8, 0))

        def confirm_and_close():
            on_confirm()
            self.destroy()

        confirm_btn = WaltButton(self.footer, text="Confirm", style="destructive", command=confirm_and_close)
        confirm_btn.pack(side="right")
