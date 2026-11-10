"""
Academic Evaluation Suite: Extraction Accuracy & Generative AI Factual Consistency.
Evaluates OCR/extraction performance against ground-truth receipts and tests AI hallucination rate.
"""
import sys
import re
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ocr.extractor import BillExtractor
from app.ai.analyzer import ExpenseAnalyzer
from app.ai.generator import get_llm_provider

# Ground-truth annotated evaluation dataset
TEST_BENCHMARK_BILLS: List[Dict[str, Any]] = [
    {
        "name": "Starbucks Cafe Receipt",
        "raw_text": """STARBUCKS COFFEE INDIA
Connaught Place, New Delhi
GSTIN: 07AAAAC1234F1Z8
Date: 04/11/2026 Time: 14:30
Invoice No: SBX-99412

Caffe Latte 1 x 280.00 = 280.00
Blueberry Muffin 1 x 220.00 = 220.00
Cold Brew 2 x 310.00 = 620.00

Sub Total: INR 1120.00
Discount: -INR 100.00
Tax / GST: INR 56.00
Service Charge: INR 50.00
Grand Total: INR 1126.00
Paid via: UPI""",
        "expected": {
            "merchant": "STARBUCKS COFFEE INDIA",
            "date": "2026-11-04",
            "total": 1126.00,
            "tax": 56.00,
            "category": "Food",
            "items": 3
        }
    },
    {
        "name": "FreshMart Supermarket Bill",
        "raw_text": """FRESHMART HYPERMARKET
Indiranagar, Bengaluru
Receipt No: FM-88210
Date: 02/11/2026

Organic Milk 2L 2 65.00 130.00
Multigrain Bread 1 55.00 55.00
Fresh Apples 1kg 1 180.00 180.00
Almonds 500g 1 450.00 450.00
Basmati Rice 5kg 1 620.00 620.00

Subtotal: INR 1435.00
Discount: -INR 85.00
Tax / GST: INR 45.00
Total Amount: INR 1395.00
Payment Method: Credit Card""",
        "expected": {
            "merchant": "FRESHMART HYPERMARKET",
            "date": "2026-11-02",
            "total": 1395.00,
            "tax": 45.00,
            "category": "Groceries",
            "items": 5
        }
    },
    {
        "name": "Shell Petroleum Fuel Bill",
        "raw_text": """SHELL PETROLEUM FUELS
Highway Station 12, Pune
Bill #: SHL-449102
Date: 05/11/2026

Power Petrol 35.5L 1 3727.50 3727.50

Sub Total: INR 3727.50
Tax / GST: INR 0.00
Grand Total: INR 3727.50
Paid via: Debit Card""",
        "expected": {
            "merchant": "SHELL PETROLEUM FUELS",
            "date": "2026-11-05",
            "total": 3727.50,
            "tax": 0.00,
            "category": "Transportation",
            "items": 1
        }
    },
    {
        "name": "Apollo Pharmacy Medical Receipt",
        "raw_text": """APOLLO PHARMACIES LTD
Koramangala, Bengaluru
Tax Invoice No: APL-60021
Date: 06/11/2026

Paracetamol 650mg 2 30.00 60.00
Vitamin C Tablets 1 150.00 150.00
Cough Syrup 1 115.00 115.00

Sub Total: INR 325.00
Tax / GST: INR 18.00
Net Amount: INR 343.00
Paid via: UPI""",
        "expected": {
            "merchant": "APOLLO PHARMACIES LTD",
            "date": "2026-11-06",
            "total": 343.00,
            "tax": 18.00,
            "category": "Healthcare",
            "items": 3
        }
    },
    {
        "name": "Zara Apparel Store Invoice",
        "raw_text": """ZARA RETAIL STORE
Select Citywalk, New Delhi
Invoice No: ZR-2026-90
Date: 05/11/2026

Textured Bomber Jacket 1 3490.00 3490.00
Slim Fit Trousers 1 1710.00 1710.00

Sub Total: INR 5200.00
Discount: -INR 500.00
Tax / GST: INR 260.00
Total Amount: INR 4960.00
Payment: Credit Card""",
        "expected": {
            "merchant": "ZARA RETAIL STORE",
            "date": "2026-11-05",
            "total": 4960.00,
            "tax": 260.00,
            "category": "Shopping",
            "items": 2
        }
    },
    {
        "name": "BESCOM Electricity Utility Bill",
        "raw_text": """BESCOM ELECTRICITY BOARD
Bangalore Electricity Supply Company
Invoice No: BES-104928
Date: 03/11/2026

Domestic Power Tariff 1 2150.00 2150.00

Sub Total: INR 2150.00
Service Charge: INR 15.00
Total Amount: INR 2165.00
Paid via: Net Banking""",
        "expected": {
            "merchant": "BESCOM ELECTRICITY BOARD",
            "date": "2026-11-03",
            "total": 2165.00,
            "tax": 0.00,
            "category": "Utilities",
            "items": 1
        }
    }
]

def run_academic_evaluation() -> Dict[str, Any]:
    """Execute quantitative extraction accuracy and AI consistency benchmarks."""
    total_bills = len(TEST_BENCHMARK_BILLS)
    correct_merchant = 0
    correct_date = 0
    correct_total = 0
    correct_tax = 0
    correct_category = 0

    print("=" * 70)
    print("STARTING ACADEMIC EVALUATION BENCHMARK")
    print(f"Dataset Size: {total_bills} Ground-Truth Annotated Invoices")
    print("=" * 70)

    for idx, bill in enumerate(TEST_BENCHMARK_BILLS, 1):
        extracted = BillExtractor.extract(bill["raw_text"])
        exp = bill["expected"]

        # Check Merchant (case-insensitive substring or match)
        m_match = exp["merchant"].lower() in extracted["merchant"].lower() or extracted["merchant"].lower() in exp["merchant"].lower()
        if m_match:
            correct_merchant += 1

        # Check Date
        d_match = str(extracted["date"]) == exp["date"]
        if d_match:
            correct_date += 1

        # Check Total
        t_match = abs(extracted["total"] - exp["total"]) <= 0.50
        if t_match:
            correct_total += 1

        # Check Tax
        tx_match = abs(extracted["tax"] - exp["tax"]) <= 0.50
        if tx_match:
            correct_tax += 1

        # Check Category
        c_match = extracted["category"].lower() == exp["category"].lower()
        if c_match:
            correct_category += 1

        print(f"[{idx}/{total_bills}] {bill['name']}:")
        print(f"   Merchant: {'PASS' if m_match else 'FAIL'} ('{extracted['merchant']}')")
        print(f"   Date:     {'PASS' if d_match else 'FAIL'} ('{extracted['date']}')")
        print(f"   Total:    {'PASS' if t_match else 'FAIL'} (Got: {extracted['total']}, Exp: {exp['total']})")
        print(f"   Tax:      {'PASS' if tx_match else 'FAIL'} (Got: {extracted['tax']}, Exp: {exp['tax']})")
        print(f"   Category: {'PASS' if c_match else 'FAIL'} ('{extracted['category']}')")

    merchant_acc = (correct_merchant / total_bills) * 100.0
    date_acc = (correct_date / total_bills) * 100.0
    total_acc = (correct_total / total_bills) * 100.0
    tax_acc = (correct_tax / total_bills) * 100.0
    cat_acc = (correct_category / total_bills) * 100.0

    print("\n" + "=" * 70)
    print("EXTRACTION ACCURACY BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"Merchant Accuracy:  {merchant_acc:.1f}% ({correct_merchant}/{total_bills})")
    print(f"Date Accuracy:      {date_acc:.1f}% ({correct_date}/{total_bills})")
    print(f"Total Amount Acc:   {total_acc:.1f}% ({correct_total}/{total_bills})")
    print(f"Tax / GST Accuracy: {tax_acc:.1f}% ({correct_tax}/{total_bills})")
    print(f"Category Accuracy:  {cat_acc:.1f}% ({correct_category}/{total_bills})")

    # Evaluate AI Factual Consistency & Hallucination Rate
    print("\n" + "=" * 70)
    print("GENERATIVE AI FACTUAL CONSISTENCY EVALUATION")
    active_prov = get_llm_provider()
    print(f"Active Provider: {active_prov.get_provider_name()}")
    print("=" * 70)

    # Synthetic context with known ground-truth metrics
    eval_context = {
        "period": "November 2026",
        "total_spending": 13716.50,
        "transaction_count": 6,
        "average_expense": 2286.08,
        "highest_expense": 4960.00,
        "top_category": "Shopping",
        "top_category_amount": 4960.00,
        "categories": [
            {"category": "Shopping", "total": 4960.00, "percentage": 36.2, "count": 1},
            {"category": "Transportation", "total": 3727.50, "percentage": 27.2, "count": 1},
            {"category": "Utilities", "total": 2165.00, "percentage": 15.8, "count": 1},
            {"category": "Groceries", "total": 1395.00, "percentage": 10.2, "count": 1},
            {"category": "Food", "total": 1126.00, "percentage": 8.2, "count": 1},
            {"category": "Healthcare", "total": 343.00, "percentage": 2.5, "count": 1}
        ],
        "top_merchants": [
            {"merchant": "ZARA RETAIL STORE", "total": 4960.00, "count": 1},
            {"merchant": "SHELL PETROLEUM FUELS", "total": 3727.50, "count": 1}
        ],
        "top_individual_expenses": [
            {"merchant": "ZARA RETAIL STORE", "category": "Shopping", "date": "2026-11-05", "amount": 4960.00},
            {"merchant": "SHELL PETROLEUM FUELS", "category": "Transportation", "date": "2026-11-05", "amount": 3727.50}
        ]
    }

    # Test Q1: Largest expense question
    ans1 = ExpenseAnalyzer.answer_expense_question("What was my largest expense?", context=eval_context)
    has_top_amount = "4,960" in ans1 or "4960" in ans1
    has_top_merchant = "ZARA" in ans1

    # Test Q2: Food spending question
    ans2 = ExpenseAnalyzer.answer_expense_question("How much did I spend on food?", context=eval_context)
    has_food_amount = "1,126" in ans2 or "1126" in ans2

    # Test Q3: Total transactions question
    ans3 = ExpenseAnalyzer.answer_expense_question("How many transactions did I make in total?", context=eval_context)
    has_tx_count = "6" in ans3

    ai_tests_passed = sum([has_top_amount and has_top_merchant, has_food_amount, has_tx_count])
    total_ai_tests = 3

    factual_consistency = (ai_tests_passed / total_ai_tests) * 100.0
    hallucination_rate = 100.0 - factual_consistency

    print(f"Q1 ('What was my largest expense?'): {'PASS' if (has_top_amount and has_top_merchant) else 'FAIL'}")
    print(f"    Answer: {ans1}")
    print(f"Q2 ('How much did I spend on food?'): {'PASS' if has_food_amount else 'FAIL'}")
    print(f"    Answer: {ans2}")
    print(f"Q3 ('How many transactions did I make?'): {'PASS' if has_tx_count else 'FAIL'}")
    print(f"    Answer: {ans3}")

    print("\nAI Benchmark Summary:")
    print(f"Factual Consistency:  {factual_consistency:.1f}%")
    print(f"Numerical Correctness: {factual_consistency:.1f}%")
    print(f"Hallucination Rate:    {hallucination_rate:.1f}%")
    print("=" * 70)

    return {
        "total_bills": total_bills,
        "merchant_accuracy": merchant_acc,
        "date_accuracy": date_acc,
        "total_accuracy": total_acc,
        "tax_accuracy": tax_acc,
        "category_accuracy": cat_acc,
        "ai_evaluation": {
            "factual_consistency": factual_consistency,
            "numerical_correctness": factual_consistency,
            "hallucination_rate": hallucination_rate
        }
    }

if __name__ == "__main__":
    run_academic_evaluation()
