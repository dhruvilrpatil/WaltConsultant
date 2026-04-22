"""Financial calculations for WaltConsultant."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class EmiSummary:
    emi_amount: float
    total_interest: float
    total_payable: float


def _money(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def add_months(source: date, months: int) -> date:
    year = source.year + ((source.month - 1 + months) // 12)
    month = ((source.month - 1 + months) % 12) + 1
    days_in_month = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day = min(source.day, days_in_month[month - 1])
    return date(year, month, day)


def calculate_emi(principal: float, annual_interest_rate: float, tenure_months: int) -> float:
    if principal <= 0:
        raise ValueError("Principal amount must be greater than zero.")
    if tenure_months <= 0:
        raise ValueError("Tenure must be greater than zero.")
    if annual_interest_rate < 0:
        raise ValueError("Interest rate cannot be negative.")

    monthly_rate = annual_interest_rate / 12 / 100
    if monthly_rate == 0:
        return _money(principal / tenure_months)

    factor = math.pow(1 + monthly_rate, tenure_months)
    emi = principal * monthly_rate * factor / (factor - 1)
    return _money(emi)


def calculate_emi_summary(principal: float, annual_interest_rate: float, tenure_months: int) -> EmiSummary:
    emi = calculate_emi(principal, annual_interest_rate, tenure_months)
    total_payable = _money(emi * tenure_months)
    total_interest = _money(total_payable - principal)
    return EmiSummary(emi_amount=emi, total_interest=total_interest, total_payable=total_payable)


def generate_amortization_schedule(
    principal: float,
    annual_interest_rate: float,
    tenure_months: int,
    first_due_date: date | str,
) -> list[dict[str, float | int | str]]:
    if isinstance(first_due_date, str):
        first_due = datetime.strptime(first_due_date, "%Y-%m-%d").date()
    else:
        first_due = first_due_date

    summary = calculate_emi_summary(principal, annual_interest_rate, tenure_months)
    monthly_rate = annual_interest_rate / 12 / 100
    balance = _money(principal)
    rows: list[dict[str, float | int | str]] = []

    for index in range(1, tenure_months + 1):
        interest = _money(balance * monthly_rate)
        principal_component = _money(summary.emi_amount - interest)

        if index == tenure_months:
            principal_component = _money(balance)
            emi_amount = _money(principal_component + interest)
        else:
            emi_amount = summary.emi_amount

        closing = _money(balance - principal_component)
        due = add_months(first_due, index - 1)

        rows.append(
            {
                "installment_number": index,
                "due_date": due.isoformat(),
                "opening_balance": _money(balance),
                "emi_amount": _money(emi_amount),
                "principal_component": principal_component,
                "interest_component": interest,
                "closing_balance": max(closing, 0.0),
                "status": "pending",
            }
        )

        balance = max(closing, 0.0)

    return rows
