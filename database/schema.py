"""Database schema and seed data for WaltConsultant."""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlite3 import Connection

import bcrypt

from utils.constants import LOAN_TYPE_SEED


def _money(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _add_months(source: date, months: int) -> date:
    year = source.year + ((source.month - 1 + months) // 12)
    month = ((source.month - 1 + months) % 12) + 1
    day = min(source.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    if tenure_months <= 0:
        raise ValueError("Tenure must be positive.")
    if principal <= 0:
        raise ValueError("Principal must be positive.")

    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        return _money(principal / tenure_months)

    factor = math.pow(1 + monthly_rate, tenure_months)
    emi = principal * monthly_rate * factor / (factor - 1)
    return _money(emi)


def build_schedule(loan_id: int, principal: float, annual_rate: float, tenure_months: int, first_due_date: date, paid_until: int = 0) -> list[tuple]:
    emi = calculate_emi(principal, annual_rate, tenure_months)
    schedule_rows: list[tuple] = []
    balance = principal
    monthly_rate = annual_rate / 12 / 100

    for i in range(1, tenure_months + 1):
        interest = _money(balance * monthly_rate)
        principal_component = _money(emi - interest)
        if i == tenure_months:
            principal_component = _money(balance)
            emi = _money(principal_component + interest)
        closing = _money(balance - principal_component)
        due = _add_months(first_due_date, i - 1)
        status = "paid" if i <= paid_until else "pending"
        schedule_rows.append(
            (
                loan_id,
                i,
                due.isoformat(),
                _money(balance),
                emi,
                principal_component,
                interest,
                max(closing, 0.0),
                status,
            )
        )
        balance = max(closing, 0.0)

    return schedule_rows


def _next_customer_id(connection: Connection) -> str:
    row = connection.execute(
        """
        SELECT COALESCE(MAX(CAST(SUBSTR(customer_id, 11) AS INTEGER)), 0) AS seq
        FROM customers
        WHERE customer_id LIKE 'WALT-CUST-%'
        """
    ).fetchone()
    seq = (row[0] if row else 0) + 1
    return f"WALT-CUST-{seq:05d}"


def _next_loan_number(connection: Connection, on_date: date) -> str:
    prefix = f"WALT-LN-{on_date.strftime('%Y%m%d')}-"
    row = connection.execute(
        """
        SELECT COALESCE(MAX(CAST(SUBSTR(loan_number, -5) AS INTEGER)), 0) AS seq
        FROM loans
        WHERE loan_number LIKE ?
        """,
        (f"{prefix}%",),
    ).fetchone()
    seq = (row[0] if row else 0) + 1
    return f"{prefix}{seq:05d}"


def create_schema(connection: Connection) -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'officer' CHECK(role IN ('admin', 'officer', 'viewer')),
            profile_photo BLOB,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            country TEXT,
            date_of_birth TEXT,
            gender TEXT,
            national_id TEXT,
            employment_status TEXT,
            organization TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            alternate_phone TEXT,
            date_of_birth TEXT,
            gender TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            country TEXT DEFAULT 'India',
            national_id_type TEXT,
            national_id_number TEXT,
            employment_status TEXT,
            employer_name TEXT,
            monthly_income REAL,
            credit_score INTEGER,
            bank_name TEXT,
            bank_account_number TEXT,
            bank_ifsc TEXT,
            nominee_name TEXT,
            nominee_relation TEXT,
            nominee_phone TEXT,
            photo BLOB,
            id_document BLOB,
            created_by INTEGER REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            notes TEXT,
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS loan_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            min_amount REAL,
            max_amount REAL,
            min_tenure_months INTEGER,
            max_tenure_months INTEGER,
            base_interest_rate REAL,
            processing_fee_percent REAL,
            description TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL REFERENCES customers(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            loan_type_id INTEGER NOT NULL REFERENCES loan_types(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            principal_amount REAL NOT NULL CHECK(principal_amount > 0),
            interest_rate REAL NOT NULL CHECK(interest_rate >= 0),
            tenure_months INTEGER NOT NULL CHECK(tenure_months > 0),
            emi_amount REAL NOT NULL,
            processing_fee REAL,
            total_payable REAL,
            disbursement_date TEXT,
            first_emi_date TEXT,
            last_emi_date TEXT,
            purpose TEXT,
            collateral_type TEXT,
            collateral_value REAL,
            collateral_description TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'disbursed', 'active', 'closed', 'rejected', 'defaulted')),
            approved_by INTEGER REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
            approved_at TIMESTAMP,
            created_by INTEGER REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            remarks TEXT,
            is_deleted INTEGER DEFAULT 0 CHECK(is_deleted IN (0, 1))
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS repayments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repayment_id TEXT UNIQUE NOT NULL,
            loan_id INTEGER NOT NULL REFERENCES loans(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            customer_id INTEGER NOT NULL REFERENCES customers(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            installment_number INTEGER,
            due_date TEXT,
            paid_date TEXT,
            principal_component REAL,
            interest_component REAL,
            emi_amount REAL,
            late_fee REAL DEFAULT 0,
            total_paid REAL,
            payment_mode TEXT,
            transaction_reference TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'overdue', 'partial', 'waived')),
            collected_by INTEGER REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            remarks TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS loan_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL REFERENCES loans(id) ON UPDATE CASCADE ON DELETE CASCADE,
            installment_number INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            opening_balance REAL,
            emi_amount REAL,
            principal_component REAL,
            interest_component REAL,
            closing_balance REAL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'overdue', 'partial', 'waived')),
            UNIQUE(loan_id, installment_number)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT UNIQUE,
            reference_type TEXT,
            reference_id INTEGER,
            document_name TEXT,
            document_type TEXT,
            file_data BLOB,
            file_name TEXT,
            file_size INTEGER,
            uploaded_by INTEGER REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
            action TEXT,
            module TEXT,
            record_id INTEGER,
            old_value TEXT,
            new_value TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
            title TEXT,
            message TEXT,
            type TEXT CHECK(type IN ('info', 'warning', 'success', 'danger')),
            is_read INTEGER DEFAULT 0 CHECK(is_read IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    ]

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_customers_customer_id ON customers(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
        "CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status)",
        "CREATE INDEX IF NOT EXISTS idx_loans_customer_status ON loans(customer_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_repayments_loan_status ON repayments(loan_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_schedule_loan_due ON loan_schedule(loan_id, due_date)",
        "CREATE INDEX IF NOT EXISTS idx_audit_module_record ON audit_log(module, record_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)",
    ]

    for statement in statements:
        connection.execute(statement)

    for statement in indexes:
        connection.execute(statement)


def seed_initial_data(connection: Connection) -> None:
    admin_exists = connection.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1").fetchone()
    if not admin_exists:
        password_hash = bcrypt.hashpw("Admin@123".encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        connection.execute(
            """
            INSERT INTO users (full_name, email, username, password_hash, role, country, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("Walt Admin", "admin@waltconsultant.local", "admin", password_hash, "admin", "India", 1),
        )

    for loan_type in LOAN_TYPE_SEED:
        connection.execute(
            """
            INSERT OR IGNORE INTO loan_types (
                name,
                min_amount,
                max_amount,
                min_tenure_months,
                max_tenure_months,
                base_interest_rate,
                processing_fee_percent,
                description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            loan_type,
        )

    customer_count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    if customer_count == 0:
        sample_customers = [
            ("Aarav Mehta", "aarav.mehta@email.com", "9876543210", "Mumbai", "Maharashtra", "400001", 782, 85000),
            ("Ishita Sharma", "ishita.sharma@email.com", "9898981212", "Pune", "Maharashtra", "411001", 736, 65000),
            ("Rohan Iyer", "rohan.iyer@email.com", "9811122233", "Bengaluru", "Karnataka", "560001", 801, 120000),
            ("Neha Kapoor", "neha.kapoor@email.com", "9797979797", "Delhi", "Delhi", "110001", 688, 54000),
            ("Vikram Singh", "vikram.singh@email.com", "9712345678", "Jaipur", "Rajasthan", "302001", 721, 72000),
        ]
        admin_id = connection.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()[0]

        for full_name, email, phone, city, state, pincode, score, income in sample_customers:
            connection.execute(
                """
                INSERT INTO customers (
                    customer_id,
                    full_name,
                    email,
                    phone,
                    city,
                    state,
                    pincode,
                    country,
                    employment_status,
                    monthly_income,
                    credit_score,
                    created_by,
                    is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _next_customer_id(connection),
                    full_name,
                    email,
                    phone,
                    city,
                    state,
                    pincode,
                    "India",
                    "Employed",
                    income,
                    score,
                    admin_id,
                    1,
                ),
            )

    loan_count = connection.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
    if loan_count > 0:
        return

    admin_id = connection.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()[0]
    customers = connection.execute("SELECT id FROM customers ORDER BY id LIMIT 3").fetchall()
    loan_type_map = {
        row["name"]: row["id"]
        for row in connection.execute("SELECT id, name FROM loan_types WHERE name IN ('Personal Loan', 'Home Loan', 'Business Loan')").fetchall()
    }

    sample_loans = [
        {
            "customer_id": customers[0]["id"],
            "loan_type": "Personal Loan",
            "principal": 350000,
            "rate": 12.5,
            "tenure": 24,
            "months_back": 10,
            "status": "active",
            "paid_installments": 8,
            "purpose": "Home renovation",
        },
        {
            "customer_id": customers[1]["id"],
            "loan_type": "Home Loan",
            "principal": 2200000,
            "rate": 8.8,
            "tenure": 180,
            "months_back": 2,
            "status": "approved",
            "paid_installments": 0,
            "purpose": "Apartment purchase",
        },
        {
            "customer_id": customers[2]["id"],
            "loan_type": "Business Loan",
            "principal": 800000,
            "rate": 13.2,
            "tenure": 12,
            "months_back": 16,
            "status": "closed",
            "paid_installments": 12,
            "purpose": "Machinery upgrade",
        },
    ]

    for data in sample_loans:
        disbursement = _add_months(date.today(), -data["months_back"])
        first_due = _add_months(disbursement, 1)
        last_due = _add_months(first_due, data["tenure"] - 1)
        emi = calculate_emi(data["principal"], data["rate"], data["tenure"])
        total_payable = _money(emi * data["tenure"])
        processing_fee = _money(data["principal"] * 0.015)

        loan_number = _next_loan_number(connection, disbursement)
        connection.execute(
            """
            INSERT INTO loans (
                loan_number,
                customer_id,
                loan_type_id,
                principal_amount,
                interest_rate,
                tenure_months,
                emi_amount,
                processing_fee,
                total_payable,
                disbursement_date,
                first_emi_date,
                last_emi_date,
                purpose,
                status,
                approved_by,
                approved_at,
                created_by,
                remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                loan_number,
                data["customer_id"],
                loan_type_map[data["loan_type"]],
                data["principal"],
                data["rate"],
                data["tenure"],
                emi,
                processing_fee,
                total_payable,
                disbursement.isoformat(),
                first_due.isoformat(),
                last_due.isoformat(),
                data["purpose"],
                data["status"],
                admin_id,
                datetime.utcnow().isoformat(timespec="seconds"),
                admin_id,
                "Seeded data",
            ),
        )
        loan_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]

        schedule_rows = build_schedule(
            loan_id=loan_id,
            principal=data["principal"],
            annual_rate=data["rate"],
            tenure_months=data["tenure"],
            first_due_date=first_due,
            paid_until=data["paid_installments"],
        )
        connection.executemany(
            """
            INSERT INTO loan_schedule (
                loan_id,
                installment_number,
                due_date,
                opening_balance,
                emi_amount,
                principal_component,
                interest_component,
                closing_balance,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            schedule_rows,
        )

        if data["paid_installments"] > 0:
            paid_rows = [row for row in schedule_rows if row[1] <= data["paid_installments"]]
            for row in paid_rows:
                connection.execute(
                    """
                    INSERT INTO repayments (
                        repayment_id,
                        loan_id,
                        customer_id,
                        installment_number,
                        due_date,
                        paid_date,
                        principal_component,
                        interest_component,
                        emi_amount,
                        late_fee,
                        total_paid,
                        payment_mode,
                        transaction_reference,
                        status,
                        collected_by,
                        remarks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"WALT-RPY-{loan_id:02d}{row[1]:03d}",
                        loan_id,
                        data["customer_id"],
                        row[1],
                        row[2],
                        row[2],
                        row[5],
                        row[6],
                        row[4],
                        0,
                        row[4],
                        "UPI",
                        f"SEED-{loan_id}-{row[1]}",
                        "paid",
                        admin_id,
                        "Seeded repayment",
                    ),
                )

    connection.execute(
        """
        INSERT INTO notifications (user_id, title, message, type)
        VALUES (?, ?, ?, ?)
        """,
        (admin_id, "Welcome", "WaltConsultant setup completed successfully.", "success"),
    )
