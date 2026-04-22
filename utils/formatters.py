"""Formatting helpers for WaltConsultant."""

from __future__ import annotations

from datetime import datetime

from babel.numbers import format_currency as babel_format_currency


def format_inr(amount: float, compact: bool = False) -> str:
    if compact:
        abs_amount = abs(amount)
        sign = "-" if amount < 0 else ""
        if abs_amount >= 10_000_000:
            return f"{sign}Rs {abs_amount / 10_000_000:.2f} Cr"
        if abs_amount >= 100_000:
            return f"{sign}Rs {abs_amount / 100_000:.2f} L"
        return f"{sign}Rs {abs_amount:,.2f}"

    try:
        return babel_format_currency(amount, "INR", locale="en_IN")
    except Exception:
        return f"Rs {amount:,.2f}"


def format_percentage(value: float) -> str:
    return f"{value:.2f}%"


def format_date_display(value: str | None) -> str:
    if not value:
        return "-"
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return value


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def safe_float(value: str | float | int | None, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: str | float | int | None, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default
