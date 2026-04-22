"""Toast notifications for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from utils.theme import PALETTE


TYPE_COLORS = {
    "info": PALETTE.primary,
    "warning": PALETTE.warning,
    "success": PALETTE.success,
    "danger": PALETTE.danger,
}


class WaltToast:
    def __init__(self, parent: tk.Tk | tk.Toplevel, message: str, type: str = "info", duration_ms: int = 3000):
        self.parent = parent
        self.message = message
        self.type = type if type in TYPE_COLORS else "info"
        self.duration_ms = duration_ms
        self.window: tk.Toplevel | None = None

    def show(self) -> None:
        toast = tk.Toplevel(self.parent)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=TYPE_COLORS[self.type])

        label = tk.Label(
            toast,
            text=self.message,
            fg="#FFFFFF",
            bg=TYPE_COLORS[self.type],
            font=("SF Pro Rounded", 11, "normal"),
            padx=12,
            pady=8,
        )
        label.pack(fill="both", expand=True)

        toast.update_idletasks()
        root_x = self.parent.winfo_rootx()
        root_y = self.parent.winfo_rooty()
        root_w = self.parent.winfo_width()
        root_h = self.parent.winfo_height()
        x = root_x + root_w - toast.winfo_width() - 20
        y = root_y + root_h - toast.winfo_height() - 20
        toast.geometry(f"+{x}+{y}")

        self.window = toast
        toast.after(self.duration_ms, self.destroy)

    def destroy(self) -> None:
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None
