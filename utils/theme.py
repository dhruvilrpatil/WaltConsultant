"""Visual design tokens and ttk style setup for WaltConsultant."""

from __future__ import annotations

import ctypes
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from tkinter import Tk, font
from tkinter import ttk


@dataclass(frozen=True)
class Palette:
    window_bg: str = "#FFFFFF"
    sidebar_bg: str = "#F5F5F7"
    primary: str = "#0071E3"
    primary_hover: str = "#0077ED"
    danger: str = "#FF3B30"
    success: str = "#34C759"
    warning: str = "#FF9F0A"
    divider: str = "#E5E5EA"
    text_primary: str = "#1D1D1F"
    text_secondary: str = "#6E6E73"
    text_tertiary: str = "#AEAEB2"
    input_bg: str = "#F2F2F7"
    selected_bg: str = "#E8F0FE"


@dataclass(frozen=True)
class Spacing:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 20
    xxl: int = 24


@dataclass(frozen=True)
class Radius:
    card: int = 10
    input: int = 10
    button: int = 8
    badge: int = 6


@dataclass(frozen=True)
class Sizing:
    sidebar_width: int = 220
    topbar_height: int = 52
    input_height: int = 36
    button_height: int = 36
    secondary_button_height: int = 32


THEME_LIGHT = "light"
THEME_DARK = "dark"


def _theme_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "theme_config.json"


def _normalize_theme_mode(mode: str | None) -> str:
    value = (mode or "").strip().lower()
    if value in {THEME_LIGHT, THEME_DARK}:
        return value
    return THEME_LIGHT


def _load_theme_mode() -> str:
    config_path = _theme_config_path()
    if not config_path.exists():
        return THEME_LIGHT
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        return _normalize_theme_mode(str(payload.get("mode", THEME_LIGHT)))
    except Exception:
        return THEME_LIGHT


def get_theme_mode() -> str:
    return _load_theme_mode()


def is_dark_mode() -> bool:
    return _CURRENT_THEME_MODE == THEME_DARK


def save_theme_mode(mode: str) -> None:
    normalized = _normalize_theme_mode(mode)
    config_path = _theme_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({"mode": normalized}, indent=2), encoding="utf-8")


LIGHT_PALETTE = Palette()
DARK_PALETTE = Palette(
    window_bg="#131722",
    sidebar_bg="#171B26",
    primary="#3A8DFF",
    primary_hover="#5AA0FF",
    danger="#FF5C5C",
    success="#3DDC84",
    warning="#FFB547",
    divider="#2A3142",
    text_primary="#E9EEF7",
    text_secondary="#A8B2C5",
    text_tertiary="#73809B",
    input_bg="#1D2432",
    selected_bg="#23324A",
)

_CURRENT_THEME_MODE = _load_theme_mode()
PALETTE = DARK_PALETTE if _CURRENT_THEME_MODE == THEME_DARK else LIGHT_PALETTE
SPACING = Spacing()
RADIUS = Radius()
SIZING = Sizing()


_BUNDLED_FONT_FILES = (
    "SF-Pro-Rounded-Regular.otf",
    "SF-Pro-Rounded-Bold.otf",
)


def _register_bundled_fonts() -> None:
    """Register bundled font files for this process on Windows."""
    if sys.platform != "win32":
        return

    fonts_dir = Path(__file__).resolve().parents[1] / "assets" / "fonts"
    if not fonts_dir.exists():
        return

    fr_private = 0x10
    wm_fontchange = 0x001D
    smto_abortifhung = 0x0002

    try:
        gdi32 = ctypes.windll.gdi32  # type: ignore[attr-defined]
        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    except Exception:
        return

    registered_any = False
    for filename in _BUNDLED_FONT_FILES:
        font_path = fonts_dir / filename
        if not font_path.exists():
            continue

        try:
            added_count = gdi32.AddFontResourceExW(str(font_path), fr_private, 0)
        except Exception:
            added_count = 0

        if added_count > 0:
            registered_any = True

    if registered_any:
        try:
            user32.SendMessageTimeoutW(0xFFFF, wm_fontchange, 0, 0, smto_abortifhung, 1000, 0)
        except Exception:
            pass


def _pick_font_family(candidates: list[str]) -> str:
    available = {family.lower(): family for family in font.families()}
    for name in candidates:
        hit = available.get(name.lower())
        if hit:
            return hit
    return "Arial"


def create_font_tokens(root: Tk) -> dict[str, tuple[str, int, str]]:
    _ = root
    _register_bundled_fonts()

    if sys.platform == "win32":
        display = _pick_font_family(["Segoe UI", "Segoe UI Variable Display", "SF Pro Rounded", "Arial"])
        text = _pick_font_family(["Segoe UI", "Segoe UI Variable Text", "SF Pro Rounded", "Arial"])
    else:
        display = _pick_font_family(["SF Pro Rounded", "SF Pro Text", "Helvetica Neue", "Arial"])
        text = _pick_font_family(["SF Pro Rounded", "SF Pro Display", "Helvetica Neue", "Arial"])

    return {
        "title": (display, 22, "bold"),
        "heading": (display, 16, "bold"),
        "body": (text, 13, "normal"),
        "caption": (text, 11, "normal"),
        "input": (text, 13, "normal"),
    }


def setup_ttk_styles(root: Tk) -> dict[str, tuple[str, int, str]]:
    """Configure global ttk styles to avoid default Tk appearance."""
    fonts = create_font_tokens(root)
    dark_mode = is_dark_mode()

    root.option_add("*Font", fonts["body"])
    root.option_add("*Menu.Font", fonts["body"])
    style = ttk.Style(root)

    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(".", background=PALETTE.window_bg, foreground=PALETTE.text_primary)
    style.configure("TFrame", background=PALETTE.window_bg)
    style.configure("Card.TFrame", background=PALETTE.window_bg, bordercolor=PALETTE.divider, relief="solid", borderwidth=1)

    style.configure("Title.TLabel", background=PALETTE.window_bg, foreground=PALETTE.text_primary, font=fonts["title"])
    style.configure("Heading.TLabel", background=PALETTE.window_bg, foreground=PALETTE.text_primary, font=fonts["heading"])
    style.configure("Body.TLabel", background=PALETTE.window_bg, foreground=PALETTE.text_primary, font=fonts["body"])
    style.configure("Caption.TLabel", background=PALETTE.window_bg, foreground=PALETTE.text_secondary, font=fonts["caption"])
    style.configure("Error.TLabel", background=PALETTE.window_bg, foreground=PALETTE.danger, font=fonts["caption"])

    tree_bg = "#151C2A" if dark_mode else PALETTE.window_bg
    tree_alt_bg = "#1A2334" if dark_mode else "#FAFBFD"
    heading_bg = "#263246" if dark_mode else PALETTE.input_bg
    heading_bg_active = "#2D3B52" if dark_mode else "#E7EAF0"
    heading_fg = "#D2DAEA" if dark_mode else PALETTE.text_secondary
    selected_bg = "#2E4568" if dark_mode else PALETTE.selected_bg

    style.configure(
        "Walt.Treeview",
        background=tree_bg,
        foreground=PALETTE.text_primary,
        selectforeground=PALETTE.text_primary,
        selectbackground=selected_bg,
        rowheight=34,
        fieldbackground=tree_bg,
        borderwidth=0,
        font=fonts["body"],
    )
    style.configure(
        "Walt.Treeview.Heading",
        background=heading_bg,
        foreground=heading_fg,
        font=fonts["caption"],
        relief="flat",
    )
    style.map(
        "Walt.Treeview.Heading",
        background=[("pressed", heading_bg_active), ("active", heading_bg_active)],
        foreground=[("pressed", PALETTE.text_primary), ("active", PALETTE.text_primary)],
    )
    style.map(
        "Walt.Treeview",
        background=[("selected", selected_bg), ("!selected", tree_bg)],
        foreground=[("selected", PALETTE.text_primary), ("!selected", PALETTE.text_primary)],
    )

    style.configure("Walt.Treeview.Even", background=tree_alt_bg, foreground=PALETTE.text_primary)
    style.configure("Walt.Treeview.Odd", background=tree_bg, foreground=PALETTE.text_primary)

    style.configure("Walt.Vertical.TScrollbar", troughcolor=PALETTE.window_bg, background=PALETTE.divider)
    style.configure("Walt.Horizontal.TScrollbar", troughcolor=PALETTE.window_bg, background=PALETTE.divider)

    style.configure("Walt.TNotebook", background=PALETTE.window_bg, borderwidth=0)
    style.configure("Walt.TNotebook.Tab", background=PALETTE.input_bg, foreground=PALETTE.text_primary, font=fonts["body"], padding=(12, 8))
    style.map("Walt.TNotebook.Tab", background=[("selected", PALETTE.window_bg)])

    style.configure(
        "Walt.TCombobox",
        fieldbackground=PALETTE.input_bg,
        background=PALETTE.input_bg,
        foreground=PALETTE.text_primary,
        bordercolor=PALETTE.divider,
        lightcolor=PALETTE.divider,
        darkcolor=PALETTE.divider,
        arrowsize=13,
        padding=6,
        relief="flat",
    )
    style.map(
        "Walt.TCombobox",
        fieldbackground=[("readonly", PALETTE.input_bg)],
        selectbackground=[("readonly", PALETTE.selected_bg)],
        selectforeground=[("readonly", PALETTE.text_primary)],
    )

    entry_bg = PALETTE.input_bg
    entry_border = PALETTE.divider
    entry_focus = PALETTE.primary

    style.configure(
        "Walt.TEntry",
        fieldbackground=entry_bg,
        foreground=PALETTE.text_primary,
        insertcolor=PALETTE.text_primary,
        bordercolor=entry_border,
        lightcolor=entry_border,
        darkcolor=entry_border,
        padding=6,
        relief="flat",
    )
    style.map(
        "Walt.TEntry",
        bordercolor=[("focus", entry_focus), ("!focus", entry_border)],
        lightcolor=[("focus", entry_focus), ("!focus", entry_border)],
        darkcolor=[("focus", entry_focus), ("!focus", entry_border)],
    )

    style.configure(
        "Walt.DateEntry",
        fieldbackground=entry_bg,
        background=entry_bg,
        foreground=PALETTE.text_primary,
        insertcolor=PALETTE.text_primary,
        bordercolor=entry_border,
        lightcolor=entry_border,
        darkcolor=entry_border,
        arrowsize=12,
        padding=6,
        relief="flat",
    )
    style.map(
        "Walt.DateEntry",
        fieldbackground=[("readonly", entry_bg), ("!readonly", entry_bg)],
        foreground=[("readonly", PALETTE.text_primary), ("!readonly", PALETTE.text_primary)],
        bordercolor=[("focus", entry_focus), ("!focus", entry_border)],
        lightcolor=[("focus", entry_focus), ("!focus", entry_border)],
        darkcolor=[("focus", entry_focus), ("!focus", entry_border)],
    )

    return fonts
