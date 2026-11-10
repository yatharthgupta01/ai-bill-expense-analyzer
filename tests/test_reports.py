"""
Unit tests for Monthly Report compilation and PDF artifact export.
"""
from pathlib import Path
from app.services.report_service import ReportService

def test_monthly_report_and_pdf_generation():
    # Compile report for November 2026
    report_data = ReportService.generate_report_data(year=2026, month=11, provider_name="local_grounded")
    assert report_data["month_label"] == "November 2026"
    assert "overview" in report_data
    assert "ai_summary" in report_data
    assert "ai_insights" in report_data

    # Export PDF artifact
    pdf_path_str = ReportService.export_pdf_report(report_data)
    pdf_path = Path(pdf_path_str)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000  # valid PDF with content
