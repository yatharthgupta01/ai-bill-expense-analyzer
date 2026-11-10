"""
Generative AI Expense Analysis and Grounded Question Answering Engine.
Computes true financial metrics from the database before LLM prompting to prevent hallucinations.
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import date, timedelta
import re

from app.database.repository import ExpenseRepository
from app.ai.generator import get_llm_provider
from app.ai.prompts import (
    EXPENSE_SUMMARY_PROMPT,
    SPENDING_INSIGHTS_PROMPT,
    SPENDING_PATTERNS_PROMPT,
    SUGGESTIONS_PROMPT,
    QA_PROMPT,
    MONTHLY_REPORT_PROMPT,
    SYSTEM_SAFETY_INSTRUCTIONS,
    FINANCIAL_SAFETY_DISCLAIMER
)
from app.utils.helpers import format_currency

class ExpenseAnalyzer:
    """Core AI analysis and conversational QA engine."""

    @staticmethod
    def prepare_spending_context(start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Aggregate ground-truth financial statistics from the database.
        This structured data forms the grounding context for LLM generation.
        """
        stats = ExpenseRepository.get_summary_stats(start_date, end_date)
        cat_breakdown = ExpenseRepository.get_category_breakdown(start_date, end_date)
        merchants = ExpenseRepository.get_merchant_breakdown(start_date, end_date, limit=5)
        dow = ExpenseRepository.get_day_of_week_breakdown(start_date, end_date)
        top_expenses = ExpenseRepository.list_expenses(
            start_date=start_date,
            end_date=end_date,
            order_by="total_desc",
            limit=5
        )

        # Calculate month-over-month comparison if analyzing current month
        today = date.today()
        ref_start = start_date or date(today.year, today.month, 1)
        prev_month_end = ref_start - timedelta(days=1)
        prev_month_start = date(prev_month_end.year, prev_month_end.month, 1)

        prev_stats = ExpenseRepository.get_summary_stats(prev_month_start, prev_month_end)
        prev_total = prev_stats["total_spending"]
        curr_total = stats["total_spending"]

        delta_spending = round(curr_total - prev_total, 2)
        pct_change = round(((curr_total - prev_total) / prev_total * 100.0), 1) if prev_total > 0 else 0.0

        # Weekend vs Weekday percentages
        weekday_tot = dow.get("weekday_total", 0.0)
        weekend_tot = dow.get("weekend_total", 0.0)
        tot_dow = weekday_tot + weekend_tot
        weekday_pct = round((weekday_tot / tot_dow * 100.0), 1) if tot_dow > 0 else 0.0
        weekend_pct = round((weekend_tot / tot_dow * 100.0), 1) if tot_dow > 0 else 0.0

        return {
            "period": f"{start_date.isoformat() if start_date else 'All'} to {end_date.isoformat() if end_date else 'Present'}",
            "total_spending": stats["total_spending"],
            "transaction_count": stats["transaction_count"],
            "average_expense": stats["average_expense"],
            "highest_expense": stats["highest_expense"],
            "top_category": stats["top_category"],
            "top_category_amount": stats["top_category_amount"],
            "categories": cat_breakdown,
            "top_merchants": merchants,
            "previous_month_total": prev_total,
            "delta_spending": delta_spending,
            "pct_change": pct_change,
            "weekday_total": weekday_tot,
            "weekend_total": weekend_tot,
            "weekday_percentage": weekday_pct,
            "weekend_percentage": weekend_pct,
            "top_individual_expenses": [
                {
                    "merchant": exp.merchant,
                    "date": exp.date.isoformat(),
                    "category": exp.category,
                    "amount": exp.total
                }
                for exp in top_expenses
            ]
        }

    @classmethod
    def format_context_string(cls, context: Dict[str, Any]) -> str:
        """Format the context dictionary into a clean markdown document for the LLM."""
        cat_str = "\n".join([
            f"  - {c['category']}: ₹{c['total']:,.2f} ({c['percentage']}%, {c['count']} txns)"
            for c in context.get("categories", [])
        ]) or "  - None"

        merchant_str = "\n".join([
            f"  - {m['merchant']}: ₹{m['total']:,.2f} ({m['count']} txns)"
            for m in context.get("top_merchants", [])
        ]) or "  - None"

        top_exp_str = "\n".join([
            f"  - {e['merchant']} ({e['category']}) on {e['date']}: ₹{e['amount']:,.2f}"
            for e in context.get("top_individual_expenses", [])
        ]) or "  - None"

        return f"""Financial Grounding Data ({context.get('period', 'Current Period')}):
- Total Expenditure: ₹{context.get('total_spending', 0.0):,.2f}
- Transaction Count: {context.get('transaction_count', 0)}
- Average Transaction: ₹{context.get('average_expense', 0.0):,.2f}
- Highest Single Transaction: ₹{context.get('highest_expense', 0.0):,.2f}
- Top Category: {context.get('top_category', 'None')} (₹{context.get('top_category_amount', 0.0):,.2f})
- Previous Period Spending: ₹{context.get('previous_month_total', 0.0):,.2f} (Delta: ₹{context.get('delta_spending', 0.0):,.2f}, Change: {context.get('pct_change', 0.0)}%)
- Day-of-Week Breakdown: Weekday ₹{context.get('weekday_total', 0.0):,.2f} ({context.get('weekday_percentage', 0)}%), Weekend ₹{context.get('weekend_total', 0.0):,.2f} ({context.get('weekend_percentage', 0)}%)

Category Distribution:
{cat_str}

Top Merchants:
{merchant_str}

Top Individual Expenses:
{top_exp_str}"""

    @classmethod
    def generate_expense_analysis(
        cls,
        context: Optional[Dict[str, Any]] = None,
        provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete AI analysis: Executive Summary, Insights, Patterns, and Suggestions.
        """
        if context is None:
            context = cls.prepare_spending_context()

        # Handle empty database
        if context.get("transaction_count", 0) == 0:
            return {
                "summary": "No expense records found for the selected period. Upload bills or seed sample data to generate AI insights.",
                "insights": "Please upload bills or invoices to begin tracking trends.",
                "patterns": "Spending pattern analysis will appear once transactions are recorded.",
                "suggestions": "Begin by uploading your grocery or utility bills to build a baseline spending history.",
                "context": context,
                "provider_used": "None (No Data)",
                "disclaimer": FINANCIAL_SAFETY_DISCLAIMER
            }

        context_str = cls.format_context_string(context)
        llm = get_llm_provider(provider_name)

        # 1. Summary
        summary_prompt = EXPENSE_SUMMARY_PROMPT.format(context=context_str)
        summary = llm.generate(summary_prompt, system_prompt=SYSTEM_SAFETY_INSTRUCTIONS)

        # 2. Insights
        insights_prompt = SPENDING_INSIGHTS_PROMPT.format(context=context_str)
        insights = llm.generate(insights_prompt, system_prompt=SYSTEM_SAFETY_INSTRUCTIONS)

        # 3. Patterns
        patterns_prompt = SPENDING_PATTERNS_PROMPT.format(context=context_str)
        patterns = llm.generate(patterns_prompt, system_prompt=SYSTEM_SAFETY_INSTRUCTIONS)

        # 4. Suggestions
        suggestions_prompt = SUGGESTIONS_PROMPT.format(context=context_str)
        suggestions = llm.generate(suggestions_prompt, system_prompt=SYSTEM_SAFETY_INSTRUCTIONS)

        return {
            "summary": summary,
            "insights": insights,
            "patterns": patterns,
            "suggestions": suggestions,
            "context": context,
            "provider_used": llm.get_provider_name(),
            "disclaimer": FINANCIAL_SAFETY_DISCLAIMER
        }

    @classmethod
    def answer_expense_question(
        cls,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        provider_name: Optional[str] = None
    ) -> str:
        """
        Answer user questions with strict grounding on actual financial records.
        For factual numerical questions, query exact figures first before synthesizing answer.
        """
        if not question or not question.strip():
            return "Please ask a question regarding your expenses."

        if context is None:
            context = cls.prepare_spending_context()

        if context.get("transaction_count", 0) == 0:
            return "You currently have no expenses recorded. Please upload bills or add expenses to ask questions about your spending."

        q_lower = question.lower().strip()

        # Deterministic Grounded Fast-Path for exact numerical questions
        # 1. Largest / Highest expense
        if any(w in q_lower for w in ["largest expense", "highest expense", "biggest expense", "most expensive item"]):
            top_exps = context.get("top_individual_expenses", [])
            if top_exps:
                top = top_exps[0]
                return (
                    f"Your largest single expense was **₹{top['amount']:,.2f}** at **{top['merchant']}** "
                    f"in the **{top['category']}** category on {top['date']}."
                )

        # 2. Top category / Where spent the most
        if any(w in q_lower for w in ["spent the most", "largest category", "highest category", "top category", "most money"]):
            top_cat = context.get("top_category")
            top_amt = context.get("top_category_amount", 0.0)
            tot = context.get("total_spending", 1.0)
            pct = round((top_amt / tot * 100.0), 1) if tot > 0 else 0.0
            return (
                f"You spent the most in **{top_cat}**, totaling **₹{top_amt:,.2f}**, "
                f"which accounts for **{pct}%** of your total spending."
            )

        # 3. Category specific questions: e.g. "How much did I spend on food?"
        categories = context.get("categories", [])
        for cat_info in categories:
            cat_name = cat_info["category"].lower()
            if cat_name in q_lower or (cat_name == "food" and "dining" in q_lower):
                return (
                    f"You spent a total of **₹{cat_info['total']:,.2f}** on **{cat_info['category']}** "
                    f"across **{cat_info['count']} transactions** ({cat_info['percentage']}% of total expenses)."
                )

        # 4. Compare this month with last month
        if any(w in q_lower for w in ["compare", "last month", "previous month", "month over month"]):
            curr = context.get("total_spending", 0.0)
            prev = context.get("previous_month_total", 0.0)
            diff = context.get("delta_spending", 0.0)
            pct = context.get("pct_change", 0.0)
            dir_str = "increased" if diff > 0 else "decreased"
            return (
                f"This month your spending is **₹{curr:,.2f}**, compared to **₹{prev:,.2f}** last month. "
                f"Your spending has **{dir_str} by ₹{abs(diff):,.2f} ({abs(pct)}%)**."
            )

        # 5. Transaction count
        if any(w in q_lower for w in ["how many transactions", "number of transactions", "how many bills", "transaction count"]):
            return f"You made a total of **{context.get('transaction_count', 0)} transactions** during this period."

        # 6. Top 5 expenses
        if any(w in q_lower for w in ["top five", "top 5", "top expenses"]):
            top_exps = context.get("top_individual_expenses", [])
            lines = [f"{idx+1}. **{e['merchant']}** ({e['category']}) - ₹{e['amount']:,.2f} on {e['date']}" for idx, e in enumerate(top_exps)]
            return "Here are your top expenses:\n\n" + "\n".join(lines)

        # 7. Total spending
        if any(w in q_lower for w in ["total spend", "how much did i spend in total", "total expenses", "total bill"]):
            return (
                f"Your total spending for this period is **₹{context.get('total_spending', 0.0):,.2f}** "
                f"across **{context.get('transaction_count', 0)} transactions**."
            )

        # For conversational or conceptual questions, prompt the Generative AI model
        context_str = cls.format_context_string(context)
        llm = get_llm_provider(provider_name)
        prompt = QA_PROMPT.format(context=context_str, question=question)
        response = llm.generate(prompt, system_prompt=SYSTEM_SAFETY_INSTRUCTIONS)
        return response
