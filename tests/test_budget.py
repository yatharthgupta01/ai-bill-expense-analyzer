"""
Unit tests for the Budget management and threshold alert calculations.
"""
from datetime import date
from app.database.repository import BudgetRepository, ExpenseRepository

def test_budget_threshold_alerts():
    month = "2026-11"
    # Set overall budget
    BudgetRepository.set_budget(month, amount=10000.0, category=None)
    # Set Food budget
    BudgetRepository.set_budget(month, amount=2000.0, category="Food")

    status = BudgetRepository.get_budget_status(month)
    assert status["overall"]["budget"] == 10000.0

    food_b = next((c for c in status["categories"] if c["category"] == "Food"), None)
    assert food_b is not None
    assert food_b["budget"] == 2000.0
    assert "is_warning" in food_b
    assert "is_exceeded" in food_b
