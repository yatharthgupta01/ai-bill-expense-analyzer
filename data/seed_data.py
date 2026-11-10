"""
Realistic synthetic sample data generator for college demonstrations and testing.
Populates diverse expense transactions across 3 months and configures baseline budgets.
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import date, timedelta
from typing import List, Dict, Any
from app.database.database import init_db
from app.database.repository import ExpenseRepository, BudgetRepository
from app.utils.helpers import get_month_key

SAMPLE_EXPENSES: List[Dict[str, Any]] = [
    # --- Month: November 2026 (Current) ---
    {
        "merchant": "FreshMart Supermarket",
        "date": date(2026, 11, 6),
        "category": "Groceries",
        "subtotal": 2450.00,
        "tax": 122.50,
        "discount": 100.00,
        "additional_charges": 0.0,
        "total": 2472.50,
        "payment_method": "UPI",
        "invoice_number": "FM-90214",
        "notes": "Weekly household groceries and essentials",
        "items": [
            {"item_name": "Organic Whole Milk 2L", "quantity": 2.0, "unit_price": 70.0, "total_price": 140.0},
            {"item_name": "Basmati Rice 5kg", "quantity": 1.0, "unit_price": 650.0, "total_price": 650.0},
            {"item_name": "Olive Oil 1L", "quantity": 1.0, "unit_price": 850.0, "total_price": 850.0},
            {"item_name": "Assorted Fresh Fruits", "quantity": 1.0, "unit_price": 450.0, "total_price": 450.0},
            {"item_name": "Dry Fruits & Nuts", "quantity": 1.0, "unit_price": 360.0, "total_price": 360.0}
        ]
    },
    {
        "merchant": "Starbucks Coffee",
        "date": date(2026, 11, 7),  # Weekend
        "category": "Food",
        "subtotal": 820.00,
        "tax": 41.00,
        "discount": 0.0,
        "additional_charges": 20.0,
        "total": 881.00,
        "payment_method": "UPI",
        "invoice_number": "SBX-8820",
        "notes": "Weekend coffee and croissant",
        "items": [
            {"item_name": "Caramel Macchiato", "quantity": 2.0, "unit_price": 310.0, "total_price": 620.0},
            {"item_name": "Almond Croissant", "quantity": 1.0, "unit_price": 200.0, "total_price": 200.0}
        ]
    },
    {
        "merchant": "Zara Retail Store",
        "date": date(2026, 11, 5),
        "category": "Shopping",
        "subtotal": 5200.00,
        "tax": 260.00,
        "discount": 500.00,
        "additional_charges": 0.0,
        "total": 4960.00,
        "payment_method": "Credit Card",
        "invoice_number": "ZR-2026-90",
        "notes": "Winter apparel jacket and formal trousers",
        "items": [
            {"item_name": "Textured Bomber Jacket", "quantity": 1.0, "unit_price": 3490.0, "total_price": 3490.0},
            {"item_name": "Slim Fit Trousers", "quantity": 1.0, "unit_price": 1710.0, "total_price": 1710.0}
        ]
    },
    {
        "merchant": "BESCOM Electricity Board",
        "date": date(2026, 11, 3),
        "category": "Utilities",
        "subtotal": 2150.00,
        "tax": 0.0,
        "discount": 0.0,
        "additional_charges": 15.0,
        "total": 2165.00,
        "payment_method": "Net Banking",
        "invoice_number": "BES-104928",
        "notes": "Monthly domestic electricity consumption",
        "items": [
            {"item_name": "Domestic Power Tariff", "quantity": 1.0, "unit_price": 2150.0, "total_price": 2150.0}
        ]
    },
    {
        "merchant": "Swiggy Food Delivery",
        "date": date(2026, 11, 4),
        "category": "Food",
        "subtotal": 450.00,
        "tax": 22.50,
        "discount": 50.00,
        "additional_charges": 35.0,
        "total": 457.50,
        "payment_method": "UPI",
        "invoice_number": "SWG-88129",
        "notes": "Dinner order",
        "items": [
            {"item_name": "Paneer Tikka Roll", "quantity": 2.0, "unit_price": 225.0, "total_price": 450.0}
        ]
    },
    {
        "merchant": "Uber India Systems",
        "date": date(2026, 11, 6),
        "category": "Transportation",
        "subtotal": 420.00,
        "tax": 21.00,
        "discount": 0.0,
        "additional_charges": 0.0,
        "total": 441.00,
        "payment_method": "UPI",
        "invoice_number": "UBR-772910",
        "notes": "Commute to college project lab",
        "items": [
            {"item_name": "Uber Premier Ride", "quantity": 1.0, "unit_price": 420.0, "total_price": 420.0}
        ]
    },
    {
        "merchant": "Apollo Pharmacy",
        "date": date(2026, 11, 2),
        "category": "Healthcare",
        "subtotal": 680.00,
        "tax": 34.00,
        "discount": 30.00,
        "additional_charges": 0.0,
        "total": 684.00,
        "payment_method": "Cash",
        "invoice_number": "APL-5521",
        "notes": "First aid supplies and multivitamins",
        "items": [
            {"item_name": "Multivitamin Capsules 60s", "quantity": 1.0, "unit_price": 450.0, "total_price": 450.0},
            {"item_name": "Antiseptic Bandages & Ointment", "quantity": 1.0, "unit_price": 230.0, "total_price": 230.0}
        ]
    },
    {
        "merchant": "PVR Cinemas Multiplex",
        "date": date(2026, 11, 7),  # Weekend
        "category": "Entertainment",
        "subtotal": 1100.00,
        "tax": 198.00,
        "discount": 0.0,
        "additional_charges": 50.0,
        "total": 1348.00,
        "payment_method": "Credit Card",
        "invoice_number": "PVR-4491",
        "notes": "Movie tickets and popcorn",
        "items": [
            {"item_name": "IMAX Recliner Tickets", "quantity": 2.0, "unit_price": 450.0, "total_price": 900.0},
            {"item_name": "Salted Popcorn Tub", "quantity": 1.0, "unit_price": 200.0, "total_price": 200.0}
        ]
    },
    {
        "merchant": "Coursera Inc",
        "date": date(2026, 11, 1),
        "category": "Education",
        "subtotal": 3200.00,
        "tax": 576.00,
        "discount": 0.0,
        "additional_charges": 0.0,
        "total": 3776.00,
        "payment_method": "Credit Card",
        "invoice_number": "CRS-99214",
        "notes": "Deep Learning & GenAI Specialization Certification",
        "items": [
            {"item_name": "Monthly Learning Pass", "quantity": 1.0, "unit_price": 3200.0, "total_price": 3200.0}
        ]
    },

    # --- Month: October 2026 ---
    {
        "merchant": "Amazon India",
        "date": date(2026, 10, 18),
        "category": "Shopping",
        "subtotal": 7890.00,
        "tax": 1420.20,
        "discount": 800.00,
        "additional_charges": 0.0,
        "total": 8510.20,
        "payment_method": "Credit Card",
        "invoice_number": "AMZ-2026-10492",
        "notes": "Ergonomic study chair and wireless keyboard",
        "items": [
            {"item_name": "Ergonomic Mesh Chair", "quantity": 1.0, "unit_price": 6490.0, "total_price": 6490.0},
            {"item_name": "Wireless Mechanical Keyboard", "quantity": 1.0, "unit_price": 1400.0, "total_price": 1400.0}
        ]
    },
    {
        "merchant": "DMart Hypermarket",
        "date": date(2026, 10, 12),
        "category": "Groceries",
        "subtotal": 3850.00,
        "tax": 192.50,
        "discount": 250.00,
        "additional_charges": 0.0,
        "total": 3792.50,
        "payment_method": "Debit Card",
        "invoice_number": "DMT-7841",
        "notes": "Monthly pantry restocking",
        "items": [
            {"item_name": "Atta 10kg", "quantity": 1.0, "unit_price": 420.0, "total_price": 420.0},
            {"item_name": "Sunflower Oil 5L", "quantity": 1.0, "unit_price": 750.0, "total_price": 750.0},
            {"item_name": "Detergent & House Cleaning Kit", "quantity": 1.0, "unit_price": 890.0, "total_price": 890.0},
            {"item_name": "Assorted Dal & Pulses", "quantity": 4.0, "unit_price": 180.0, "total_price": 720.0},
            {"item_name": "Snacks & Biscuits", "quantity": 1.0, "unit_price": 1070.0, "total_price": 1070.0}
        ]
    },
    {
        "merchant": "Airtel Broadband",
        "date": date(2026, 10, 10),
        "category": "Utilities",
        "subtotal": 999.00,
        "tax": 179.82,
        "discount": 0.0,
        "additional_charges": 0.0,
        "total": 1178.82,
        "payment_method": "UPI",
        "invoice_number": "AIR-882194",
        "notes": "Xstream Fiber 200Mbps Monthly Bill",
        "items": [
            {"item_name": "Broadband Monthly Rental", "quantity": 1.0, "unit_price": 999.0, "total_price": 999.0}
        ]
    },
    {
        "merchant": "Barbeque Nation",
        "date": date(2026, 10, 24),  # Weekend
        "category": "Food",
        "subtotal": 2400.00,
        "tax": 120.00,
        "discount": 200.00,
        "additional_charges": 120.0,
        "total": 2440.00,
        "payment_method": "Credit Card",
        "invoice_number": "BBQ-49102",
        "notes": "Family weekend buffet dinner",
        "items": [
            {"item_name": "Non-Veg Dinner Buffet", "quantity": 2.0, "unit_price": 1200.0, "total_price": 2400.0}
        ]
    },
    {
        "merchant": "HPCL Petrol Pump",
        "date": date(2026, 10, 15),
        "category": "Transportation",
        "subtotal": 2500.00,
        "tax": 0.0,
        "discount": 0.0,
        "additional_charges": 0.0,
        "total": 2500.00,
        "payment_method": "UPI",
        "invoice_number": "HPC-55910",
        "notes": "Vehicle fuel refill",
        "items": [
            {"item_name": "Petrol", "quantity": 24.5, "unit_price": 102.04, "total_price": 2500.0}
        ]
    },

    # --- Month: September 2026 ---
    {
        "merchant": "MakeMyTrip Travel",
        "date": date(2026, 9, 20),
        "category": "Travel",
        "subtotal": 6500.00,
        "tax": 325.00,
        "discount": 400.00,
        "additional_charges": 50.0,
        "total": 6475.00,
        "payment_method": "Net Banking",
        "invoice_number": "MMT-90021",
        "notes": "Weekend college trek train tickets and homestay reservation",
        "items": [
            {"item_name": "IRCTC Train Express Tickets", "quantity": 2.0, "unit_price": 1250.0, "total_price": 2500.0},
            {"item_name": "Homestay Booking 2 Nights", "quantity": 1.0, "unit_price": 4000.0, "total_price": 4000.0}
        ]
    },
    {
        "merchant": "Reliance Digital",
        "date": date(2026, 9, 14),
        "category": "Shopping",
        "subtotal": 4500.00,
        "tax": 810.00,
        "discount": 300.00,
        "additional_charges": 0.0,
        "total": 5010.00,
        "payment_method": "Credit Card",
        "invoice_number": "RD-2026-449",
        "notes": "External SSD drive 1TB for AI project datasets",
        "items": [
            {"item_name": "Samsung T7 1TB Portable SSD", "quantity": 1.0, "unit_price": 4500.0, "total_price": 4500.0}
        ]
    },
    {
        "merchant": "Haldirams Restaurant",
        "date": date(2026, 9, 27),
        "category": "Food",
        "subtotal": 750.00,
        "tax": 37.50,
        "discount": 0.0,
        "additional_charges": 0.0,
        "total": 787.50,
        "payment_method": "UPI",
        "invoice_number": "HLD-88210",
        "notes": "Snacks and thali",
        "items": [
            {"item_name": "Special Raj Kachori", "quantity": 2.0, "unit_price": 180.0, "total_price": 360.0},
            {"item_name": "Executive Thali", "quantity": 1.0, "unit_price": 390.0, "total_price": 390.0}
        ]
    }
]

def seed_sample_expenses():
    """Populate database with realistic synthetic expense transactions and baseline budgets."""
    init_db()
    ExpenseRepository.clear_all_expenses()

    # Insert sample expenses
    for exp_data in SAMPLE_EXPENSES:
        items = exp_data.get("items", [])
        ExpenseRepository.create_expense(exp_data, items=items)

    # Configure realistic budgets for November 2026
    current_month = "2026-11"
    BudgetRepository.set_budget(current_month, amount=22000.0, category=None)  # Overall
    BudgetRepository.set_budget(current_month, amount=3000.0, category="Food")
    BudgetRepository.set_budget(current_month, amount=3500.0, category="Groceries")
    BudgetRepository.set_budget(current_month, amount=5000.0, category="Shopping")
    BudgetRepository.set_budget(current_month, amount=2500.0, category="Utilities")
    BudgetRepository.set_budget(current_month, amount=2000.0, category="Transportation")

    print(f"Successfully seeded {len(SAMPLE_EXPENSES)} realistic expense transactions and baseline budgets.")

if __name__ == "__main__":
    seed_sample_expenses()
