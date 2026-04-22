"""Validation utilities for WaltConsultant forms."""

from __future__ import annotations

import re
from typing import Any

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^[6-9][0-9]{9}$")
PINCODE_REGEX = re.compile(r"^[1-9][0-9]{5}$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.-]{4,32}$")


def is_required(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone.strip()))


def is_valid_pincode(pincode: str) -> bool:
    return bool(PINCODE_REGEX.match(pincode.strip()))


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_REGEX.match(username.strip()))


def password_strength(password: str) -> tuple[int, str]:
    score = 0
    if len(password) >= 8:
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"[a-z]", password):
        score += 1
    if re.search(r"[0-9]", password):
        score += 1
    if re.search(r"[^A-Za-z0-9]", password):
        score += 1

    label = "Weak"
    if score >= 5:
        label = "Very Strong"
    elif score == 4:
        label = "Strong"
    elif score == 3:
        label = "Fair"

    return score, label


def validate_signup_fields(payload: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}

    if not is_required(payload.get("full_name")):
        errors["full_name"] = "Full name is required."

    username = str(payload.get("username", "")).strip()
    if not is_valid_username(username):
        errors["username"] = "Username must be 4-32 chars and may include . _ -."

    email = str(payload.get("email", "")).strip()
    if not is_valid_email(email):
        errors["email"] = "Enter a valid email address."

    password = str(payload.get("password", ""))
    score, _ = password_strength(password)
    if score < 3:
        errors["password"] = "Password must include upper/lowercase, number and special char."

    if password != str(payload.get("confirm_password", "")):
        errors["confirm_password"] = "Passwords do not match."

    phone = str(payload.get("phone", "")).strip()
    if phone and not is_valid_phone(phone):
        errors["phone"] = "Enter a valid 10-digit Indian phone number."

    pincode = str(payload.get("pincode", "")).strip()
    if pincode and not is_valid_pincode(pincode):
        errors["pincode"] = "Enter a valid 6-digit pincode."

    return errors


def validate_customer_fields(payload: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}

    if not is_required(payload.get("full_name")):
        errors["full_name"] = "Customer name is required."

    email = str(payload.get("email", "")).strip()
    if not is_valid_email(email):
        errors["email"] = "Valid customer email is required."

    phone = str(payload.get("phone", "")).strip()
    if not is_valid_phone(phone):
        errors["phone"] = "Valid customer phone is required."

    if payload.get("pincode") and not is_valid_pincode(str(payload["pincode"])):
        errors["pincode"] = "Pincode must be 6 digits."

    return errors


def validate_loan_fields(payload: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}

    if not payload.get("customer_id"):
        errors["customer_id"] = "Customer is required."

    if not payload.get("loan_type_id"):
        errors["loan_type_id"] = "Loan type is required."

    principal = float(payload.get("principal_amount", 0) or 0)
    rate = float(payload.get("interest_rate", 0) or 0)
    tenure = int(payload.get("tenure_months", 0) or 0)

    if principal <= 0:
        errors["principal_amount"] = "Principal amount must be greater than zero."

    if rate < 0:
        errors["interest_rate"] = "Interest rate cannot be negative."

    if tenure <= 0:
        errors["tenure_months"] = "Tenure must be greater than zero."

    return errors
