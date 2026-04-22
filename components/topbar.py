"""Top navigation bar component for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from components.avatar import WaltAvatarCircle
from utils.constants import APP_NAME
from utils.theme import PALETTE, SIZING


class WaltTopBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=PALETTE.window_bg, height=SIZING.topbar_height, highlightthickness=1, highlightbackground=PALETTE.divider)
        self.pack_propagate(False)

        left = tk.Frame(self, bg=PALETTE.window_bg)
        left.pack(side="left", fill="y", padx=16)

        right = tk.Frame(self, bg=PALETTE.window_bg)
        right.pack(side="right", fill="y", padx=16)

        self.app_label = tk.Label(left, text=APP_NAME, bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 13, "bold"))
        self.app_label.pack(side="left", padx=(0, 14))

        self.page_title = tk.Label(left, text="Dashboard", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 12))
        self.page_title.pack(side="left")

        self.user_name = tk.Label(right, text="Guest", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 11))
        self.user_name.pack(side="right", padx=(8, 0))

        self.avatar = WaltAvatarCircle(right, name="Guest", size=30)
        self.avatar.pack(side="right")

    def set_page_title(self, title: str) -> None:
        self.page_title.configure(text=title)

    def set_user(self, name: str, photo_bytes: bytes | None = None) -> None:
        self.user_name.configure(text=name)
        self.avatar.render(name=name, photo_bytes=photo_bytes)
