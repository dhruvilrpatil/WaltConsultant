"""Entry point for WaltConsultant desktop application."""

from __future__ import annotations

import ctypes
import sys
import tkinter as tk

from app import WaltConsultantApp


def _configure_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return

    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):  # type: ignore[attr-defined]
            return
    except Exception:
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # type: ignore[attr-defined]
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()  # type: ignore[attr-defined]
    except Exception:
        pass


def main() -> None:
    _configure_windows_dpi_awareness()
    root = tk.Tk()
    scaling = root.winfo_fpixels("1i") / 72.0
    root.call("tk", "scaling", max(1.0, round(scaling * 4) / 4))
    WaltConsultantApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
