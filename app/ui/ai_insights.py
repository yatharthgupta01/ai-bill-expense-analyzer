"""
Generative AI Insights and Conversational Q&A View.
Empowers users to generate deep natural-language spending analysis and ask interactive questions.
"""
import streamlit as st
import os

from app.ai.analyzer import ExpenseAnalyzer
from app.utils.helpers import get_date_range_preset

MODEL_CHOICES = {
    "Local HuggingFace Transformer (FLAN-T5)": "local_flan",
    "Grounded Contextual Engine (Offline / Instant / 0 Hallucination)": "local_grounded",
    "Google Gemini API (Cloud)": "gemini",
    "OpenAI GPT API (Cloud)": "openai"
}

QUICK_QUESTIONS = [
    "Where did I spend the most this month?",
    "How much did I spend on food?",
    "What was my largest expense?",
    "Compare this month with last month.",
    "What were my top five expenses?",
    "How many transactions did I make in total?",
    "What are my major spending patterns?"
]

def render_ai_insights():
    """Render Generative AI spending analysis and interactive Q&A assistant."""
    st.markdown("## 🤖 Generative AI Spending Insights & Assistant")
    st.caption("Pretrained Transformer-powered deep financial analysis, behavioral patterns, and grounded Q&A.")

    # Model & Range Selection
    with st.expander("⚙️ AI Model & Grounding Scope Settings", expanded=True):
        m_col1, m_col2 = st.columns([3, 2])
        with m_col1:
            provider_label = st.selectbox(
                "Select Generative AI Inference Provider",
                list(MODEL_CHOICES.keys()),
                index=0,
                help="Switch between local offline transformer-grounded inference and external APIs."
            )
            selected_provider_key = MODEL_CHOICES[provider_label]

            # If Gemini/OpenAI selected, check for API key
            if selected_provider_key == "gemini" and not os.getenv("GEMINI_API_KEY"):
                api_input = st.text_input("Enter Gemini API Key (or set GEMINI_API_KEY in .env):", type="password")
                if api_input:
                    os.environ["GEMINI_API_KEY"] = api_input
            elif selected_provider_key == "openai" and not os.getenv("OPENAI_API_KEY"):
                api_input = st.text_input("Enter OpenAI API Key (or set OPENAI_API_KEY in .env):", type="password")
                if api_input:
                    os.environ["OPENAI_API_KEY"] = api_input

        with m_col2:
            time_scope = st.selectbox("Analysis Timeframe", ["This Month", "Last 3 Months", "Previous Month", "All Time"])
            start_d, end_d = get_date_range_preset(time_scope if time_scope != "All Time" else "Last 3 Months")

    # Tabs for Analysis and Q&A
    tab_analysis, tab_qa = st.tabs(["📊 Comprehensive AI Spending Analysis", "💬 Ask About My Expenses"])

    # TAB 1: AI Spending Analysis
    with tab_analysis:
        st.markdown("#### 🔍 Natural-Language Spending Synthesis")
        st.write("Generates an executive summary, detects anomalies, explains spending patterns, and provides actionable optimization tips.")

        if st.button("✨ Generate AI Analysis Now", type="primary", key="btn_run_analysis"):
            with st.spinner("Aggregating financial context and running Generative AI model..."):
                context = ExpenseAnalyzer.prepare_spending_context(start_d, end_d)
                analysis_results = ExpenseAnalyzer.generate_expense_analysis(context, provider_name=selected_provider_key)
                st.session_state.latest_analysis = analysis_results

        if "latest_analysis" in st.session_state and st.session_state.latest_analysis:
            res = st.session_state.latest_analysis
            st.caption(f"Generated via: **{res.get('provider_used')}**")

            # 4 Distinct Cards required by Section 11
            col_a, col_b = st.columns(2)

            with col_a:
                with st.container(border=True):
                    st.markdown("### 📝 Executive Expense Summary")
                    st.write(res.get("summary"))

                with st.container(border=True):
                    st.markdown("### 📈 Spending Insights & Trends")
                    st.markdown(res.get("insights"))

            with col_b:
                with st.container(border=True):
                    st.markdown("### 🔄 Spending Pattern Explanation")
                    st.markdown(res.get("patterns"))

                with st.container(border=True):
                    st.markdown("### 💡 Practical Budget Suggestions")
                    st.markdown(res.get("suggestions"))

            # Safety Disclaimer Banner (Section 25)
            st.warning(f"⚖️ **Financial Disclaimer:** {res.get('disclaimer')}")

    # TAB 2: Ask About My Expenses (Section 12)
    with tab_qa:
        st.markdown("#### 💬 Conversational Expense Assistant")
        st.caption("Ask questions in natural language. Answers are computed strictly from your actual financial records.")

        # Quick Suggested Prompts
        st.write("**Frequently Asked Questions (Click to ask):**")
        p_cols = st.columns(len(QUICK_QUESTIONS[:4]))
        for idx, prompt_text in enumerate(QUICK_QUESTIONS[:4]):
            if p_cols[idx].button(f"👉 {prompt_text}", key=f"quick_btn_{idx}"):
                st.session_state.chat_query_input = prompt_text

        # Chat history state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": "Hello! I am your AI Expense Assistant. Ask me anything about your recorded transactions, category totals, or spending trends."
                }
            ]

        # Display history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat Input
        user_query = st.chat_input("Ask a question about your expenses (e.g. 'How much did I spend on food?')...")
        if "chat_query_input" in st.session_state and st.session_state.chat_query_input:
            user_query = st.session_state.chat_query_input
            st.session_state.chat_query_input = None

        if user_query:
            # Append user message
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Generate grounded answer
            with st.chat_message("assistant"):
                with st.spinner("Analyzing records..."):
                    context = ExpenseAnalyzer.prepare_spending_context(start_d, end_d)
                    answer = ExpenseAnalyzer.answer_expense_question(
                        user_query,
                        context=context,
                        provider_name=selected_provider_key
                    )
                    st.markdown(answer)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    st.caption("⚡ Answer verified against database aggregates.")
