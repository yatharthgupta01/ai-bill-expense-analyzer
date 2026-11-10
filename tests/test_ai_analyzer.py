"""
Unit tests for the Generative AI analysis, Local FLAN-T5 Transformer, and grounded conversational Q&A system.
"""
import pytest
from app.ai.generator import get_llm_provider, LocalFlanT5Provider, GroundedLocalProvider
from app.ai.analyzer import ExpenseAnalyzer

def test_spending_context_preparation():
    """Verify that financial metrics context is accurately aggregated from database."""
    context = ExpenseAnalyzer.prepare_spending_context()
    assert "total_spending" in context
    assert "transaction_count" in context
    assert "average_expense" in context
    assert "top_category" in context
    assert "categories" in context

def test_local_flan_provider_selection():
    """Verify that local_flan provider can be selected explicitly and is the default."""
    provider_explicit = get_llm_provider("local_flan")
    assert isinstance(provider_explicit, LocalFlanT5Provider)
    assert "Local Transformer" in provider_explicit.get_provider_name()

    # Default provider should be LocalFlanT5Provider
    provider_default = get_llm_provider()
    assert isinstance(provider_default, LocalFlanT5Provider)

def test_local_flan_initialization_and_generation():
    """Verify that FLAN-T5 model initializes properly and generates text."""
    provider = LocalFlanT5Provider("google/flan-t5-small")
    assert provider.is_available() is True
    assert "google/flan-t5-small" in provider.get_provider_name()

    res = provider.generate("Instruction: Output the number.\nContext: Total is 42.")
    assert isinstance(res, str)
    assert len(res) > 0

def test_missing_model_graceful_fallback():
    """Verify that an invalid or un-loadable model fails gracefully without crashing."""
    provider = LocalFlanT5Provider("nonexistent/invalid-model-name")
    assert provider.is_available() is False

    # Should gracefully return fallback text from GroundedLocalProvider rather than crashing
    fallback_res = provider.generate("Summarize spending")
    assert isinstance(fallback_res, str)
    assert len(fallback_res) > 10

def test_ai_analysis_generation_flan():
    """Verify that generate_expense_analysis runs with local_flan provider."""
    analysis = ExpenseAnalyzer.generate_expense_analysis(provider_name="local_flan")
    assert "summary" in analysis
    assert "insights" in analysis
    assert "patterns" in analysis
    assert "suggestions" in analysis
    assert "disclaimer" in analysis
    assert "Local Transformer" in analysis["provider_used"]
    assert len(analysis["summary"]) > 5

def test_grounded_qa_numerical_database_values():
    """Verify that factual numerical questions strictly return database-derived values."""
    mock_context = {
        "period": "November 2026",
        "total_spending": 5000.0,
        "transaction_count": 3,
        "average_expense": 1666.67,
        "highest_expense": 3000.0,
        "top_category": "Shopping",
        "top_category_amount": 3000.0,
        "categories": [
            {"category": "Shopping", "total": 3000.0, "percentage": 60.0, "count": 1},
            {"category": "Food", "total": 2000.0, "percentage": 40.0, "count": 2}
        ],
        "top_individual_expenses": [
            {"merchant": "TechStore", "category": "Shopping", "date": "2026-11-04", "amount": 3000.0}
        ]
    }

    ans_largest = ExpenseAnalyzer.answer_expense_question("What was my largest expense?", context=mock_context)
    assert "3,000" in ans_largest or "3000" in ans_largest
    assert "TechStore" in ans_largest

    ans_food = ExpenseAnalyzer.answer_expense_question("How much did I spend on food?", context=mock_context)
    assert "2,000" in ans_food or "2000" in ans_food

    ans_txns = ExpenseAnalyzer.answer_expense_question("How many transactions did I make?", context=mock_context)
    assert "3" in ans_txns
