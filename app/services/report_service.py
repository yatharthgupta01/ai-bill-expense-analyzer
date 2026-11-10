"""
Monthly Expense Report Generator with Generative AI insights and PDF export via fpdf2.
"""
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
from fpdf import FPDF

from app.database.repository import ExpenseRepository
from app.ai.analyzer import ExpenseAnalyzer
from app.utils.helpers import format_currency

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_pdf_text(text: str) -> str:
    """Sanitize unicode characters for standard core PDF fonts."""
    if not text:
        return ""
    replacements = {
        "•": "-",
        "₹": "INR ",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "\u2022": "-",
        "\u20b9": "INR "
    }
    cleaned = text
    for orig, rep in replacements.items():
        cleaned = cleaned.replace(orig, rep)
    # Ensure all remaining chars are latin-1 compatible
    return cleaned.encode("latin-1", errors="replace").decode("latin-1")

class PDFReport(FPDF):
    """Custom FPDF2 class for generating clean, academic-grade financial reports."""

    def __init__(self, month_label: str):
        super().__init__()
        self.month_label = month_label

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 41, 59)
        self.cell(0, 10, "AI Bill & Expense Analyzer - Monthly Report", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "", 11)
        self.set_text_color(100, 116, 139)
        self.cell(0, 6, f"Period: {self.month_label} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(4)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 5, "General Personal Spending Analysis Report - Informational use only. Not certified financial advice.", new_x="LMARGIN", new_y="NEXT", align="C")
        self.cell(0, 5, f"Page {self.page_no()}", align="C")


class ReportService:
    """Generates structured monthly reports with AI narrative and compiles PDF artifacts."""

    @classmethod
    def generate_report_data(cls, year: int, month: int, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Compile complete report data including DB aggregates and AI narrative."""
        start_date = date(year, month, 1)
        next_m = month + 1 if month < 12 else 1
        next_y = year if month < 12 else year + 1
        end_date = date(next_y, next_m, 1) - timedelta(days=1)

        month_label = start_date.strftime("%B %Y")
        context = ExpenseAnalyzer.prepare_spending_context(start_date, end_date)
        ai_analysis = ExpenseAnalyzer.generate_expense_analysis(context, provider_name=provider_name)

        return {
            "year": year,
            "month": month,
            "month_label": month_label,
            "start_date": start_date,
            "end_date": end_date,
            "overview": {
                "total_spending": context["total_spending"],
                "transaction_count": context["transaction_count"],
                "average_expense": context["average_expense"],
                "highest_expense": context["highest_expense"],
                "top_category": context["top_category"],
                "top_category_amount": context["top_category_amount"]
            },
            "category_analysis": context["categories"],
            "trends": {
                "previous_month_total": context["previous_month_total"],
                "delta_spending": context["delta_spending"],
                "pct_change": context["pct_change"]
            },
            "ai_insights": ai_analysis["insights"],
            "ai_summary": ai_analysis["summary"],
            "ai_patterns": ai_analysis["patterns"],
            "suggestions": ai_analysis["suggestions"],
            "provider_used": ai_analysis["provider_used"],
            "disclaimer": ai_analysis["disclaimer"]
        }

    @classmethod
    def export_pdf_report(cls, report_data: Dict[str, Any]) -> str:
        """
        Compile report data into a PDF document using fpdf2 and save to reports/.
        Returns the absolute path to the generated PDF.
        """
        month_label = report_data["month_label"]
        pdf = PDFReport(month_label=month_label)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)

        # 1. Executive Summary Cards / Table
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "1. Executive Expense Overview", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        overview = report_data["overview"]
        pdf.set_font("Helvetica", "", 10)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)

        col_w = 47
        pdf.cell(col_w, 7, "Total Spend", border=1, fill=True, align="C")
        pdf.cell(col_w, 7, "Transactions", border=1, fill=True, align="C")
        pdf.cell(col_w, 7, "Average / Txn", border=1, fill=True, align="C")
        pdf.cell(col_w, 7, "Highest Single", border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(col_w, 8, f"INR {overview['total_spending']:,.2f}", border=1, align="C")
        pdf.cell(col_w, 8, str(overview["transaction_count"]), border=1, align="C")
        pdf.cell(col_w, 8, f"INR {overview['average_expense']:,.2f}", border=1, align="C")
        pdf.cell(col_w, 8, f"INR {overview['highest_expense']:,.2f}", border=1, align="C")
        pdf.ln(12)

        # 2. Category Analysis
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "2. Category Spending Breakdown", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(70, 7, "Category", border=1, fill=True)
        pdf.cell(40, 7, "Total Amount (INR)", border=1, fill=True, align="R")
        pdf.cell(40, 7, "Percentage (%)", border=1, fill=True, align="R")
        pdf.cell(40, 7, "Transactions", border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        categories = report_data.get("category_analysis", [])
        if categories:
            for cat in categories:
                pdf.cell(70, 6, sanitize_pdf_text(str(cat["category"])), border=1)
                pdf.cell(40, 6, f"{cat['total']:,.2f}", border=1, align="R")
                pdf.cell(40, 6, f"{cat['percentage']}%", border=1, align="R")
                pdf.cell(40, 6, str(cat["count"]), border=1, align="C")
                pdf.ln()
        else:
            pdf.cell(190, 6, "No category transactions recorded for this period.", border=1, align="C")
            pdf.ln()
        pdf.ln(8)

        # 3. Trends & Comparisons
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "3. Period Trends & Comparisons", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        trends = report_data.get("trends", {})
        delta = trends.get("delta_spending", 0.0)
        dir_sym = "+" if delta >= 0 else "-"
        pdf.set_font("Helvetica", "", 10)
        trend_txt = (
            f"Previous Month Spending: INR {trends.get('previous_month_total', 0.0):,.2f}\n"
            f"Current Month Net Difference: {dir_sym}INR {abs(delta):,.2f} ({trends.get('pct_change', 0.0)}% variation compared to previous month)."
        )
        pdf.multi_cell(0, 6, sanitize_pdf_text(trend_txt))
        pdf.ln(8)

        # 4. Generative AI Insights
        pdf.set_font("Helvetica", "B", 13)
        prov_name = sanitize_pdf_text(str(report_data.get('provider_used', 'Local')))
        pdf.cell(0, 8, f"4. Generative AI Analysis (Engine: {prov_name})", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Executive Summary:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, sanitize_pdf_text(report_data.get("ai_summary", "")))
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Key Spending Insights & Anomalies:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, sanitize_pdf_text(report_data.get("ai_insights", "")))
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Observed Spending Patterns:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, sanitize_pdf_text(report_data.get("ai_patterns", "")))
        pdf.ln(6)

        # 5. Practical Spending Suggestions
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "5. Practical Budget Optimization Suggestions", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, sanitize_pdf_text(report_data.get("suggestions", "")))
        pdf.ln(8)

        # Save to file
        safe_month = month_label.replace(" ", "_")
        filename = f"Expense_Report_{safe_month}.pdf"
        dest_path = REPORTS_DIR / filename
        pdf.output(str(dest_path))
        return str(dest_path)
