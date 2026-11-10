"""
Unit tests for the automatic expense categorization service.
"""
from app.services.categorization import categorizer

def test_categorization_domains():
    cat, conf = categorizer.categorize(merchant="Starbucks Coffee", items=["Cappuccino", "Muffin"])
    assert cat == "Food"

    cat, conf = categorizer.categorize(merchant="FreshMart Grocery", items=["Organic Milk", "Bread", "Rice"])
    assert cat == "Groceries"

    cat, conf = categorizer.categorize(merchant="Uber Technologies", items=["Uber Premier Trip"])
    assert cat == "Transportation"

    cat, conf = categorizer.categorize(merchant="Zara Apparel Mall", items=["Bomber Jacket", "Jeans"])
    assert cat == "Shopping"

    cat, conf = categorizer.categorize(merchant="BESCOM Power Supply", items=["Electricity consumption"])
    assert cat == "Utilities"

    cat, conf = categorizer.categorize(merchant="Apollo Pharmacy", items=["Antibiotics", "Bandages"])
    assert cat == "Healthcare"

    cat, conf = categorizer.categorize(merchant="Coursera Learning", items=["Python Certification"])
    assert cat == "Education"

def test_categorization_fallback():
    cat, conf = categorizer.categorize(merchant="Random Unrelated XYZ Corp", items=["Item ABC"])
    assert cat == "Other"
