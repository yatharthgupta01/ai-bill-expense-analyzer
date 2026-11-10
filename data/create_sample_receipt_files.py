"""
Generate sample PDF receipt files in data/sample_bills for user testing and evaluation.
"""
import sys
from pathlib import Path
from fpdf import FPDF

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample_bills"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

def create_receipt_pdf(filename: str, title: str, inv_no: str, date_str: str, items: list, subtotal: float, tax: float, discount: float, charges: float, total: float, payment: str):
    pdf = FPDF(unit="mm", format=(80, 160))  # Standard thermal receipt size
    pdf.add_page()
    pdf.set_margins(5, 5, 5)
    pdf.set_auto_page_break(auto=True, margin=5)

    # Header
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(70, 5, title, ln=True, align="C")
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(70, 4, "Tax Invoice / Cash Receipt", ln=True, align="C")
    pdf.cell(70, 4, f"Invoice No: {inv_no}", ln=True, align="C")
    pdf.cell(70, 4, f"Date: {date_str}  Time: 14:30", ln=True, align="C")
    pdf.line(5, pdf.get_y(), 75, pdf.get_y())
    pdf.ln(2)

    # Items Header
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(32, 4, "Item")
    pdf.cell(10, 4, "Qty", align="C")
    pdf.cell(14, 4, "Price", align="R")
    pdf.cell(14, 4, "Total", ln=True, align="R")
    pdf.line(5, pdf.get_y(), 75, pdf.get_y())
    pdf.ln(1)

    # Line Items
    pdf.set_font("Helvetica", "", 7)
    for name, qty, price, line_tot in items:
        pdf.cell(32, 4, name[:20])
        pdf.cell(10, 4, str(qty), align="C")
        pdf.cell(14, 4, f"{price:.2f}", align="R")
        pdf.cell(14, 4, f"{line_tot:.2f}", ln=True, align="R")

    pdf.line(5, pdf.get_y(), 75, pdf.get_y())
    pdf.ln(2)

    # Summary
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(45, 4, "Sub Total:")
    pdf.cell(25, 4, f"INR {subtotal:.2f}", ln=True, align="R")

    if discount > 0:
        pdf.cell(45, 4, "Discount:")
        pdf.cell(25, 4, f"-INR {discount:.2f}", ln=True, align="R")

    if tax > 0:
        pdf.cell(45, 4, "Tax / GST:")
        pdf.cell(25, 4, f"INR {tax:.2f}", ln=True, align="R")

    if charges > 0:
        pdf.cell(45, 4, "Service Charge:")
        pdf.cell(25, 4, f"INR {charges:.2f}", ln=True, align="R")

    pdf.line(5, pdf.get_y(), 75, pdf.get_y())
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(45, 6, "Grand Total:")
    pdf.cell(25, 6, f"INR {total:.2f}", ln=True, align="R")

    pdf.set_font("Helvetica", "I", 7)
    pdf.cell(70, 4, f"Paid via: {payment}", ln=True, align="C")
    pdf.cell(70, 4, "Thank you for your visit!", ln=True, align="C")

    dest = SAMPLE_DIR / filename
    pdf.output(str(dest))
    print(f"Generated sample receipt PDF: {dest}")

if __name__ == "__main__":
    create_receipt_pdf(
        "starbucks_coffee_receipt.pdf",
        "STARBUCKS COFFEE INDIA",
        "SBX-99412",
        "04/11/2026",
        [
            ("Caffe Latte", 1, 280.0, 280.0),
            ("Blueberry Muffin", 1, 220.0, 220.0),
            ("Cold Brew", 2, 310.0, 620.0)
        ],
        subtotal=1120.0,
        tax=56.0,
        discount=100.0,
        charges=50.0,
        total=1126.0,
        payment="UPI"
    )

    create_receipt_pdf(
        "freshmart_grocery_bill.pdf",
        "FRESHMART HYPERMARKET",
        "FM-88210",
        "02/11/2026",
        [
            ("Organic Milk 2L", 2, 65.0, 130.0),
            ("Multigrain Bread", 1, 55.0, 55.0),
            ("Fresh Apples 1kg", 1, 180.0, 180.0),
            ("Almonds 500g", 1, 450.0, 450.0),
            ("Basmati Rice 5kg", 1, 620.0, 620.0)
        ],
        subtotal=1435.0,
        tax=45.0,
        discount=85.0,
        charges=0.0,
        total=1395.0,
        payment="Credit Card"
    )

    create_receipt_pdf(
        "shell_fuel_receipt.pdf",
        "SHELL PETROLEUM FUELS",
        "SHL-449102",
        "05/11/2026",
        [
            ("Power Petrol 35.5L", 1, 3727.50, 3727.50)
        ],
        subtotal=3727.50,
        tax=0.0,
        discount=0.0,
        charges=0.0,
        total=3727.50,
        payment="Debit Card"
    )
