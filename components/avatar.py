"""Avatar component for WaltConsultant."""

from __future__ import annotations

import io
import tkinter as tk

from PIL import Image, ImageDraw, ImageTk

from utils.theme import PALETTE


class WaltAvatarCircle(tk.Frame):
    def __init__(self, parent, name: str, size: int = 36, photo_bytes: bytes | None = None):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.size = size
        self.label = tk.Label(self, bg=PALETTE.window_bg)
        self.label.pack(fill="both", expand=True)
        self._photo_ref = None
        self.render(name, photo_bytes)

    def _initials(self, name: str) -> str:
        parts = [part for part in name.strip().split() if part]
        if not parts:
            return "WC"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return f"{parts[0][0]}{parts[1][0]}".upper()

    def render(self, name: str, photo_bytes: bytes | None = None) -> None:
        if photo_bytes:
            try:
                image = Image.open(io.BytesIO(photo_bytes)).convert("RGBA").resize((self.size, self.size), Image.Resampling.LANCZOS)
                mask = Image.new("L", (self.size, self.size), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, self.size - 1, self.size - 1), fill=255)
                image.putalpha(mask)
                photo = ImageTk.PhotoImage(image)
                self._photo_ref = photo
                self.label.configure(image=photo, text="")
                return
            except Exception:
                pass

        initials = self._initials(name)
        self.label.configure(
            text=initials,
            fg="#FFFFFF",
            bg=PALETTE.primary,
            font=("SF Pro Rounded", max(10, self.size // 3), "bold"),
            width=max(2, self.size // 14),
            height=max(1, self.size // 24),
        )
