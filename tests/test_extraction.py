"""
Unit tests for document parsing, information extraction, and arithmetic validation.
"""
from datetime import date
from app.ocr.extractor import BillExtractor
from app.utils.validation import validate_expense_data

def test_bill_extractor_parsing():
    raw_text = """DOMINOS PIZZA OUTLET
Connaught Place, New Delhi
Tax Invoice #: DOM-77192
Date: 05/11/2026

Peppy Paneer Pizza 2 350.00 700.00
Garlic Breadsticks 1 120.00 120.00

Sub Total: INR 820.00
GST / Tax: INR 41.00
Delivery Fee: INR 30.00
Discount: -INR 50.00
Grand Total: INR 841.00
Paid by: UPI"""

    draft = BillExtractor.extract(raw_text)

    assert "DOMINOS" in draft["merchant"].upper()
    assert draft["invoice_number"] == "DOM-77192"
    assert draft["date"] == date(2026, 11, 5)
    assert draft["subtotal"] == 820.0
    assert draft["tax"] == 41.0
    assert draft["discount"] == 50.0
    assert draft["additional_charges"] == 30.0
    assert draft["total"] == 841.0
    assert draft["category"] == "Food"
    assert len(draft["items"]) == 2

def test_validation_arithmetic():
    """Verify that arithmetic validation detects discrepancies and calculates missing subtotals."""
    # Balanced data
    valid_data = {
        "merchant": "Supermart",
        "date": date(2026, 11, 1),
        "subtotal": 100.0,
        "tax": 10.0,
        "discount": 5.0,
        "additional_charges": 0.0,
        "total": 105.0
    }
    is_valid, warnings, errors = validate_expense_data(valid_data)
    assert is_valid is True
    assert len(errors) == 0
    assert len(warnings) == 0

    # Arithmetic mismatch
    mismatched = {
        "merchant": "Supermart",
        "date": date(2026, 11, 1),
        "subtotal": 100.0,
        "tax": 10.0,
        "discount": 0.0,
        "additional_charges": 0.0,
        "total": 150.0  # Should be 110.0
    }
    is_valid, warnings, errors = validate_expense_data(mismatched)
    assert is_valid is True
    assert any("Arithmetic discrepancy" in w for w in warnings)

    # Missing merchant error
    invalid_data = {
        "merchant": "",
        "date": date(2026, 11, 1),
        "total": 100.0
    }
    is_valid, warnings, errors = validate_expense_data(invalid_data)
    assert is_valid is False
    assert any("Merchant" in e for e in errors)
