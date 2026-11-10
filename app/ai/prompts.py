"""
System prompts and prompt templates for Generative AI expense analysis.
Strictly adheres to financial safety, factual grounding, and zero-hallucination rules.
"""

FINANCIAL_SAFETY_DISCLAIMER = (
    "Note: The insights and suggestions generated are for general spending awareness and personal informational "
    "purposes only. They do not constitute certified professional financial or investment advice."
)

SYSTEM_SAFETY_INSTRUCTIONS = """You are an intelligent, objective personal finance analyst.
CRITICAL SAFETY & FACTUAL RULES:
1. Grounding: Rely strictly and exclusively on the financial metrics and transactions provided in the context.
2. No Hallucinations: NEVER invent numbers, dates, merchant names, or transactions that are not explicitly stated in the context.
3. No Investment Advice: Do not recommend purchasing stocks, mutual funds, crypto, or specific financial securities.
4. Accuracy: If the required information is not present in the context, explicitly say that the data is not available.
5. Tone: Professional, encouraging, clear, and concise."""

EXPENSE_SUMMARY_PROMPT = """Context Data:
{context}

Task:
Generate a concise, natural-language executive summary of the user's spending for this period.
Mention:
- Total expenditure and transaction count.
- The dominant spending category and its percentage share.
- General balance among other categories.
Keep it between 3 to 5 sentences. Do not invent any numbers."""

SPENDING_INSIGHTS_PROMPT = """Context Data:
{context}

Task:
Identify 2-3 meaningful spending insights and trends from the data.
Highlight:
- Any notable increases or decreases compared to previous periods or standard benchmarks.
- Any unusually large or outlier transactions.
- Category concentration risks.
Provide bullet points with clear, factual commentary."""

SPENDING_PATTERNS_PROMPT = """Context Data:
{context}

Task:
Explain the behavioral patterns in the user's spending habits based on the context:
- Weekday vs. Weekend distribution.
- Frequency of micro-transactions (e.g. food delivery, small retail) vs. planned large expenses.
- Merchant concentration (frequent visits to specific vendors).
Explain why these patterns matter for daily budgeting."""

SUGGESTIONS_PROMPT = """Context Data:
{context}

Task:
Provide 3 practical, realistic suggestions to optimize personal expenses.
Rules:
- Focus on lifestyle habits (e.g., subscription audits, reducing frequent small impulse orders, grocery batching).
- DO NOT provide stock or investment advice.
- Phrase as friendly, general spending suggestions."""

QA_PROMPT = """Context Data:
{context}

User Question:
"{question}"

Task:
Answer the user's question directly, accurately, and politely using ONLY the facts and figures provided in the context above.
If the answer is a specific number, state it clearly with the currency symbol.
If the requested information cannot be found in the context, clearly explain that it is not available in the current expense records.
Do NOT invent any financial data."""

MONTHLY_REPORT_PROMPT = """Context Data:
{context}

Task:
Generate an insightful narrative section for a Monthly Expense Report.
Structure your response into:
1. Executive Spending Review
2. Category Breakdown & Notable Variations
3. Behavioral Spending Observations
4. Practical Optimization Recommendations
Ensure all stated numbers match the context figures exactly."""
