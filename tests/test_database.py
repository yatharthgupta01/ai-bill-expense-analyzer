"""
Unit tests for database models, CRUD operations, and analytical queries.
"""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Expense, ExpenseItem, Budget
from app.database.repository import ExpenseRepository, BudgetRepository

def test_database_expense_crud():
    """Test creating, reading, updating, and deleting an expense with line items."""
    exp_data = {
        "merchant": "Test Cafe",
        "date": date(2026, 11, 1),
        "category": "Food",
        "subtotal": 200.0,
        "tax": 10.0,
        "discount": 0.0,
        "additional_charges": 0.0,
        "total": 210.0,
        "payment_method": "Cash",
        "invoice_number": "TC-001"
    }
    items = [
        {"item_name": "Espresso", "quantity": 1.0, "unit_price": 100.0, "total_price": 100.0},
        {"item_name": "Bagel", "quantity": 1.0, "unit_price": 100.0, "total_price": 100.0}
    ]

    # Create
    expense = ExpenseRepository.create_expense(exp_data, items=items)
    assert expense.id is not None
    assert expense.merchant == "Test Cafe"
    assert expense.total == 210.0
    assert len(expense.items) == 2

    # Read
    fetched = ExpenseRepository.get_expense_by_id(expense.id)
    assert fetched is not None
    assert fetched.merchant == "Test Cafe"

    # Update
    updated = ExpenseRepository.update_expense(expense.id, {"merchant": "Updated Cafe", "total": 220.0})
    assert updated.merchant == "Updated Cafe"
    assert updated.total == 220.0

    # Delete
    deleted = ExpenseRepository.delete_expense(expense.id)
    assert deleted is True
    assert ExpenseRepository.get_expense_by_id(expense.id) is None

def test_database_summary_and_aggregations():
    """Test KPI calculations and category breakdowns."""
    exp1 = ExpenseRepository.create_expense({
        "merchant": "Store A",
        "date": date(2026, 11, 2),
        "category": "Shopping",
        "subtotal": 1000.0,
        "total": 1000.0
    })
    exp2 = ExpenseRepository.create_expense({
        "merchant": "Store B",
        "date": date(2026, 11, 3),
        "category": "Food",
        "subtotal": 500.0,
        "total": 500.0
    })

    stats = ExpenseRepository.get_summary_stats(start_date=date(2026, 11, 1), end_date=date(2026, 11, 30))
    assert stats["transaction_count"] >= 2
    assert stats["total_spending"] >= 1500.0

    cats = ExpenseRepository.get_category_breakdown(start_date=date(2026, 11, 1), end_date=date(2026, 11, 30))
    cat_names = [c["category"] for c in cats]
    assert "Shopping" in cat_names
    assert "Food" in cat_names

    # Cleanup test records
    ExpenseRepository.delete_expense(exp1.id)
    ExpenseRepository.delete_expense(exp2.id)
