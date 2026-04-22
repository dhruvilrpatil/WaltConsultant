# WaltConsultant

WaltConsultant is a desktop Loan Management System built with Python, Tkinter, and SQLite.

## Tech Stack

- Python 3.10+
- Tkinter + ttk
- SQLite3
- Pillow, bcrypt, tkcalendar, fpdf2, matplotlib, babel

## Features Implemented

- Splash, login, and multi-step signup flow
- Session-based authentication with bcrypt password hashing
- Role-based access (admin, officer, viewer)
- Full SQLite schema with migrations and first-run seed data
- Dashboard metrics, charts, recent loan list, due EMI quick-pay
- Customers module (search, add, edit, deactivate, detail panel with tabs)
- Loans module (filters, creation, EMI preview, schedule generation, status updates, statement export)
- Repayments module (record payment, late fee handling, receipt generation, CSV bulk import)
- Reports module (multiple report types, preview, CSV export, PDF export)
- Documents module (upload, list, preview, download, delete)
- Settings module (profile, company settings, loan type management, user management, audit log, backup/restore)
- Custom Walt UI component library (buttons, inputs, table, modal, toast, sidebar, topbar, etc.)

## Project Structure

```
waltconsultant/
├── main.py
├── app.py
├── database/
├── models/
├── screens/
├── components/
├── utils/
├── assets/
└── requirements.txt
```

## Setup

1. Open terminal in the `waltconsultant` folder.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Default Login

- Username: `admin`
- Password: `Admin@123`

## Notes

- SQLite database file `waltconsultant.db` is auto-created in the project directory on first run.
- First run applies migrations and seeds admin/loan types/sample customers/sample loans.
- Bundled SF Pro Rounded fonts in `assets/fonts` are auto-loaded on Windows and used across the UI.
