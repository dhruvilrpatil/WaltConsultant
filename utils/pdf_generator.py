"""PDF generation for statements and receipts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fpdf import FPDF


class WaltPDFGenerator:
    def __init__(self, company_name: str = "WaltConsultant") -> None:
        self.company_name = company_name

    def _base_pdf(self, title: str) -> FPDF:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, self.company_name, ln=True)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, title, ln=True)
        pdf.ln(3)
        return pdf

    def generate_receipt(self, output_path: str | Path, receipt: dict[str, Any]) -> Path:
        pdf = self._base_pdf("Payment Receipt")
        pdf.set_font("Helvetica", "", 11)

        for key in [
            "repayment_id",
            "loan_number",
            "customer_name",
            "paid_date",
            "emi_amount",
            "late_fee",
            "total_paid",
            "payment_mode",
            "transaction_reference",
        ]:
            label = key.replace("_", " ").title()
            value = str(receipt.get(key, "-"))
            pdf.cell(60, 8, label)
            pdf.cell(0, 8, value, ln=True)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(output))
        return output

    def generate_loan_statement(self, output_path: str | Path, loan: dict[str, Any], schedule: list[dict[str, Any]]) -> Path:
        pdf = self._base_pdf("Loan Statement")
        pdf.set_font("Helvetica", "", 10)

        for key in ["loan_number", "customer_name", "principal_amount", "interest_rate", "tenure_months", "emi_amount", "status"]:
            label = key.replace("_", " ").title()
            pdf.cell(55, 7, label)
            pdf.cell(0, 7, str(loan.get(key, "-")), ln=True)

        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 9)
        headers = ["Inst#", "Due Date", "EMI", "Principal", "Interest", "Closing", "Status"]
        widths = [15, 28, 24, 24, 24, 24, 24]

        for index, header in enumerate(headers):
            pdf.cell(widths[index], 7, header, border=1, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for row in schedule:
            pdf.cell(widths[0], 6, str(row.get("installment_number", "")), border=1)
            pdf.cell(widths[1], 6, str(row.get("due_date", "")), border=1)
            pdf.cell(widths[2], 6, str(row.get("emi_amount", "")), border=1)
            pdf.cell(widths[3], 6, str(row.get("principal_component", "")), border=1)
            pdf.cell(widths[4], 6, str(row.get("interest_component", "")), border=1)
            pdf.cell(widths[5], 6, str(row.get("closing_balance", "")), border=1)
            pdf.cell(widths[6], 6, str(row.get("status", "")), border=1)
            pdf.ln()

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(output))
        return output


PDF_GENERATOR = WaltPDFGenerator()
