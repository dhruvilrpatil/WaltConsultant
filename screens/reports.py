"""Reports screen for WaltConsultant."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from fpdf import FPDF
from tkcalendar import DateEntry

from components.button import WaltButton
from components.card import WaltCard
from components.table import WaltTable
from components.toast import WaltToast
from database.connection import get_db_manager
from utils.theme import PALETTE

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False


REPORT_TYPES = [
    "Loan Portfolio Summary",
    "Customer Statement",
    "EMI Collection Report",
    "Overdue / Default Report",
    "Disbursement Report",
    "Revenue / Interest Report",
    "Officer-wise Performance",
]


class ReportsScreen(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.db = get_db_manager()
        self.current_report = REPORT_TYPES[0]
        self.current_rows: list[dict] = []
        self.current_columns: list[tuple[str, str, int]] = []
        self.table_widget: WaltTable | None = None

        self._build()
        self._run_report()

    def _toast(self, message: str, kind: str = "info") -> None:
        WaltToast(self.winfo_toplevel(), message, kind).show()

    def _build(self) -> None:
        tk.Label(self, text="Reports", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 22, "bold")).pack(anchor="w", padx=20, pady=(16, 10))

        content = tk.Frame(self, bg=PALETTE.window_bg)
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        left = WaltCard(content, padding=12)
        left.pack(side="left", fill="y", padx=(0, 12))

        tk.Label(left.content, text="Report Types", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 14, "bold")).pack(anchor="w", pady=(0, 8))

        for report_name in REPORT_TYPES:
            WaltButton(
                left.content,
                text=report_name,
                style="secondary",
                command=lambda r=report_name: self._select_report(r),
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=3)

        right = tk.Frame(content, bg=PALETTE.window_bg)
        right.pack(side="left", fill="both", expand=True)

        filters = WaltCard(right, padding=10)
        filters.pack(fill="x", pady=(0, 10))

        line1 = tk.Frame(filters.content, bg=PALETTE.window_bg)
        line1.pack(fill="x")

        tk.Label(line1, text="From", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(side="left")
        self.from_date = DateEntry(
            line1,
            date_pattern="yyyy-mm-dd",
            style="Walt.DateEntry",
            width=12,
            background=PALETTE.primary,
            foreground=PALETTE.text_primary,
            borderwidth=1,
            headersbackground=PALETTE.input_bg,
            headersforeground=PALETTE.text_primary,
            normalbackground=PALETTE.input_bg,
            normalforeground=PALETTE.text_primary,
            weekendbackground=PALETTE.input_bg,
            weekendforeground=PALETTE.text_primary,
        )
        self.from_date.pack(side="left", padx=(6, 12))

        tk.Label(line1, text="To", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(side="left")
        self.to_date = DateEntry(
            line1,
            date_pattern="yyyy-mm-dd",
            style="Walt.DateEntry",
            width=12,
            background=PALETTE.primary,
            foreground=PALETTE.text_primary,
            borderwidth=1,
            headersbackground=PALETTE.input_bg,
            headersforeground=PALETTE.text_primary,
            normalbackground=PALETTE.input_bg,
            normalforeground=PALETTE.text_primary,
            weekendbackground=PALETTE.input_bg,
            weekendforeground=PALETTE.text_primary,
        )
        self.to_date.pack(side="left", padx=(6, 12))

        self.loan_type_var = tk.StringVar(value="")
        loan_types = [""] + [row["name"] for row in self.db.fetchall("SELECT name FROM loan_types ORDER BY name")]
        self.loan_type_filter = ttk.Combobox(line1, values=loan_types, textvariable=self.loan_type_var, width=20, style="Walt.TCombobox", state="readonly")
        self.loan_type_filter.pack(side="left")

        line2 = tk.Frame(filters.content, bg=PALETTE.window_bg)
        line2.pack(fill="x", pady=(8, 0))

        WaltButton(line2, text="Preview", style="primary", command=self._run_report).pack(side="left")
        WaltButton(line2, text="Export PDF", style="secondary", command=self._export_pdf).pack(side="left", padx=(8, 0))
        WaltButton(line2, text="Export CSV", style="secondary", command=self._export_csv).pack(side="left", padx=(8, 0))

        preview_card = WaltCard(right, padding=10)
        preview_card.pack(fill="both", expand=True)

        tk.Label(preview_card.content, text="Preview", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 14, "bold")).pack(anchor="w", pady=(0, 8))

        preview_body = tk.Frame(preview_card.content, bg=PALETTE.window_bg)
        preview_body.pack(fill="both", expand=True)
        preview_body.grid_columnconfigure(0, weight=1)
        preview_body.grid_rowconfigure(0, weight=3)
        preview_body.grid_rowconfigure(1, weight=2)

        self.preview_holder = tk.Frame(preview_body, bg=PALETTE.window_bg)
        self.preview_holder.grid(row=0, column=0, sticky="nsew")

        self.chart_holder = tk.Frame(preview_body, bg=PALETTE.window_bg, height=280)
        self.chart_holder.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.chart_holder.grid_propagate(False)

    def _select_report(self, report_name: str) -> None:
        self.current_report = report_name
        self._run_report()

    def _run_report(self) -> None:
        start = self.from_date.get_date().isoformat()
        end = self.to_date.get_date().isoformat()
        loan_type = self.loan_type_var.get().strip()

        self.current_columns, self.current_rows = self._query_report(self.current_report, start, end, loan_type)
        self._render_preview()
        self._render_chart()

    def _query_report(self, report_name: str, start: str, end: str, loan_type: str) -> tuple[list[tuple[str, str, int]], list[dict]]:
        params: list = [start, end]

        type_clause = ""
        if loan_type:
            type_clause = " AND lt.name = ?"
            params.append(loan_type)

        if report_name == "Loan Portfolio Summary":
            rows = self.db.fetchall(
                f"""
                SELECT lt.name AS loan_type,
                       COUNT(l.id) AS total_loans,
                       COALESCE(SUM(l.principal_amount), 0) AS principal,
                       COALESCE(SUM(l.total_payable), 0) AS total_payable
                FROM loans l
                JOIN loan_types lt ON lt.id = l.loan_type_id
                WHERE l.created_at BETWEEN ? AND ? {type_clause}
                GROUP BY lt.name
                ORDER BY principal DESC
                """,
                tuple(params),
            )
            columns = [("loan_type", "Loan Type", 180), ("total_loans", "Loans", 90), ("principal", "Principal", 140), ("total_payable", "Total Payable", 140)]

        elif report_name == "Customer Statement":
            rows = self.db.fetchall(
                """
                SELECT c.customer_id, c.full_name,
                       COUNT(l.id) AS loans,
                       COALESCE(SUM(l.principal_amount), 0) AS principal,
                       COALESCE(SUM(r.total_paid), 0) AS collected
                FROM customers c
                LEFT JOIN loans l ON l.customer_id = c.id
                LEFT JOIN repayments r ON r.customer_id = c.id
                GROUP BY c.id
                ORDER BY principal DESC
                """
            )
            columns = [("customer_id", "Customer ID", 130), ("full_name", "Customer", 170), ("loans", "Loans", 70), ("principal", "Principal", 130), ("collected", "Collected", 130)]

        elif report_name == "EMI Collection Report":
            rows = self.db.fetchall(
                """
                SELECT strftime('%Y-%m', paid_date) AS month,
                       COUNT(id) AS repayments,
                       COALESCE(SUM(total_paid), 0) AS total_collected
                FROM repayments
                WHERE paid_date BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', paid_date)
                ORDER BY month DESC
                """,
                (start, end),
            )
            columns = [("month", "Month", 100), ("repayments", "Repayments", 110), ("total_collected", "Total Collected", 170)]

        elif report_name == "Overdue / Default Report":
            rows = self.db.fetchall(
                """
                SELECT l.loan_number, c.full_name, l.status,
                       COUNT(ls.id) AS overdue_installments,
                       COALESCE(SUM(ls.emi_amount), 0) AS overdue_amount
                FROM loans l
                JOIN customers c ON c.id = l.customer_id
                LEFT JOIN loan_schedule ls ON ls.loan_id = l.id AND ls.status = 'overdue'
                WHERE l.status IN ('defaulted', 'active', 'disbursed')
                GROUP BY l.id
                HAVING overdue_installments > 0
                ORDER BY overdue_amount DESC
                """
            )
            columns = [("loan_number", "Loan Number", 160), ("full_name", "Customer", 170), ("status", "Status", 90), ("overdue_installments", "Overdue Inst", 100), ("overdue_amount", "Overdue Amount", 140)]

        elif report_name == "Disbursement Report":
            rows = self.db.fetchall(
                f"""
                SELECT l.disbursement_date, l.loan_number, c.full_name, lt.name AS loan_type,
                       l.principal_amount, l.status
                FROM loans l
                JOIN customers c ON c.id = l.customer_id
                JOIN loan_types lt ON lt.id = l.loan_type_id
                WHERE l.disbursement_date BETWEEN ? AND ? {type_clause}
                ORDER BY l.disbursement_date DESC
                """,
                tuple(params),
            )
            columns = [("disbursement_date", "Disbursement", 110), ("loan_number", "Loan Number", 160), ("full_name", "Customer", 150), ("loan_type", "Type", 120), ("principal_amount", "Amount", 120), ("status", "Status", 90)]

        elif report_name == "Revenue / Interest Report":
            rows = self.db.fetchall(
                """
                SELECT strftime('%Y-%m', r.paid_date) AS month,
                       COALESCE(SUM(r.principal_component), 0) AS principal,
                       COALESCE(SUM(r.interest_component), 0) AS interest,
                       COALESCE(SUM(r.total_paid), 0) AS revenue
                FROM repayments r
                WHERE r.paid_date BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', r.paid_date)
                ORDER BY month DESC
                """,
                (start, end),
            )
            columns = [("month", "Month", 100), ("principal", "Principal", 120), ("interest", "Interest", 120), ("revenue", "Revenue", 120)]

        else:
            rows = self.db.fetchall(
                """
                SELECT u.full_name AS officer,
                       COUNT(DISTINCT l.id) AS loans_managed,
                       COALESCE(SUM(l.principal_amount), 0) AS principal,
                       COALESCE(SUM(r.total_paid), 0) AS collections
                FROM users u
                LEFT JOIN loans l ON l.created_by = u.id
                LEFT JOIN repayments r ON r.collected_by = u.id
                WHERE u.role IN ('admin', 'officer')
                GROUP BY u.id
                ORDER BY collections DESC
                """
            )
            columns = [("officer", "Officer", 170), ("loans_managed", "Loans", 90), ("principal", "Principal", 130), ("collections", "Collections", 130)]

        return columns, [dict(row) for row in rows]

    def _render_preview(self) -> None:
        for child in self.preview_holder.winfo_children():
            child.destroy()

        if not self.current_columns:
            tk.Label(self.preview_holder, text="No report columns", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w")
            return

        self.table_widget = WaltTable(self.preview_holder, columns=self.current_columns, data=self.current_rows)
        self.table_widget.pack(fill="both", expand=True)

    def _render_chart(self) -> None:
        for child in self.chart_holder.winfo_children():
            child.destroy()
        if not MATPLOTLIB_AVAILABLE:
            return
        if not self.current_rows:
            return

        num_columns = [c[0] for c in self.current_columns[1:] if all(self._is_number(row.get(c[0])) for row in self.current_rows)]
        if not num_columns:
            return

        x_key = self.current_columns[0][0]
        y_key = num_columns[0]
        x_values = [str(row.get(x_key, "")) for row in self.current_rows[:10]]
        y_values = [float(row.get(y_key, 0) or 0) for row in self.current_rows[:10]]

        figure = Figure(figsize=(7.8, 3.1), dpi=100)
        axis = figure.add_subplot(111)
        axis.bar(x_values, y_values, color=PALETTE.primary)
        axis.set_title(f"{self.current_report} - {y_key}", color=PALETTE.text_primary, fontsize=10, pad=14)
        axis.set_facecolor(PALETTE.window_bg)
        figure.patch.set_facecolor(PALETTE.window_bg)
        axis.tick_params(axis="x", rotation=25, labelsize=8, colors=PALETTE.text_secondary)
        axis.tick_params(axis="y", labelsize=8, colors=PALETTE.text_secondary)
        axis.grid(axis="y", linestyle="--", linewidth=0.7, color=PALETTE.divider, alpha=0.7)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color(PALETTE.divider)
        axis.spines["bottom"].set_color(PALETTE.divider)
        figure.tight_layout(pad=1.35)

        canvas = FigureCanvasTkAgg(figure, master=self.chart_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    @staticmethod
    def _is_number(value) -> bool:
        try:
            float(value)
            return True
        except Exception:
            return False

    def _export_csv(self) -> None:
        if not self.current_rows:
            self._toast("No report data to export", "warning")
            return

        output = Path(__file__).resolve().parents[1] / "exports" / f"report_{self.current_report.replace(' ', '_')}_{date.today().isoformat()}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[col[0] for col in self.current_columns])
            writer.writeheader()
            for row in self.current_rows:
                writer.writerow(row)

        self._toast(f"CSV exported: {output.name}", "success")

    def _export_pdf(self) -> None:
        if not self.current_rows:
            self._toast("No report data to export", "warning")
            return

        output = Path(__file__).resolve().parents[1] / "exports" / f"report_{self.current_report.replace(' ', '_')}_{date.today().isoformat()}.pdf"
        output.parent.mkdir(parents=True, exist_ok=True)

        pdf = FPDF(orientation="L")
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 10, f"WaltConsultant - {self.current_report}", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 8, f"Date range: {self.from_date.get_date().isoformat()} to {self.to_date.get_date().isoformat()}", ln=True)
        pdf.ln(2)

        headers = [col[1] for col in self.current_columns]
        fields = [col[0] for col in self.current_columns]
        width = max(25, int(275 / max(1, len(headers))))

        pdf.set_font("Helvetica", "B", 8)
        for header in headers:
            pdf.cell(width, 7, str(header), border=1)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for row in self.current_rows[:200]:
            for field in fields:
                text = str(row.get(field, ""))
                if len(text) > 20:
                    text = text[:20] + "..."
                pdf.cell(width, 6, text, border=1)
            pdf.ln()

        pdf.output(str(output))
        self._toast(f"PDF exported: {output.name}", "success")
