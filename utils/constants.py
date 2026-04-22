"""Shared constants for WaltConsultant domain and UI behavior."""

from __future__ import annotations

APP_NAME = "WaltConsultant"
APP_TAGLINE = "Loan Management, Simplified."
DB_FILE_NAME = "waltconsultant.db"

ROLES = ["admin", "officer", "viewer"]

ROLE_PERMISSIONS = {
    "admin": {
        "customers": ["read", "create", "update", "delete"],
        "loans": ["read", "create", "update", "delete", "approve", "disburse", "close"],
        "repayments": ["read", "create", "update", "delete"],
        "reports": ["read", "export"],
        "documents": ["read", "create", "delete"],
        "settings": ["read", "update"],
        "users": ["read", "create", "update", "delete"],
    },
    "officer": {
        "customers": ["read", "create", "update", "delete"],
        "loans": ["read", "create", "update", "approve", "disburse"],
        "repayments": ["read", "create", "update"],
        "reports": ["read", "export"],
        "documents": ["read", "create"],
        "settings": ["read", "update"],
        "users": ["read"],
    },
    "viewer": {
        "customers": ["read"],
        "loans": ["read"],
        "repayments": ["read"],
        "reports": ["read"],
        "documents": ["read"],
        "settings": ["read"],
        "users": ["read"],
    },
}

GENDERS = ["Male", "Female", "Other"]

NATIONAL_ID_TYPES = ["Aadhar", "PAN", "Passport", "Voter ID"]

EMPLOYMENT_STATUSES = [
    "Employed",
    "Self-Employed",
    "Business",
    "Student",
    "Retired",
]

PAYMENT_MODES = ["Cash", "UPI", "NEFT", "IMPS", "Cheque", "DD"]

LOAN_STATUSES = ["pending", "approved", "disbursed", "active", "closed", "rejected", "defaulted"]

REPAYMENT_STATUSES = ["pending", "paid", "overdue", "partial", "waived"]

NOTIFICATION_TYPES = ["info", "warning", "success", "danger"]

LOAN_TYPE_SEED = [
    ("Personal Loan", 10000, 2500000, 6, 84, 12.5, 2.0, "Unsecured personal financing"),
    ("Home Loan", 500000, 50000000, 60, 360, 8.5, 1.2, "Long tenure housing finance"),
    ("Vehicle Loan", 50000, 5000000, 12, 84, 10.5, 1.8, "Two/four wheeler financing"),
    ("Business Loan", 100000, 20000000, 12, 120, 14.0, 2.5, "Working capital and expansion"),
    ("Education Loan", 100000, 5000000, 12, 180, 9.0, 1.0, "Higher education finance"),
    ("Gold Loan", 5000, 5000000, 3, 36, 10.0, 1.0, "Gold-backed short-term finance"),
    ("Agricultural Loan", 20000, 10000000, 6, 120, 8.0, 0.8, "Crop and farm development"),
]

INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
]

SIDEBAR_ITEMS = [
    "Dashboard",
    "Customers",
    "Loans",
    "Repayments",
    "Reports",
    "Documents",
    "Settings",
    "Logout",
]
