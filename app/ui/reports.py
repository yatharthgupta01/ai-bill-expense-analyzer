"""
Monthly Expense Report View: Comprehensive review and PDF artifact export.
"""
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path

from app.services.report_service import ReportService
from app.ai.generator import BaseLLMProvider

def render_reports():
    """Render the monthly report generation and PDF export interface."""
    st.markdown("## 📑 Monthly Expense Reports")
    st.caption("Generate publication-ready monthly financial reports featuring automated calculations, AI narratives, and PDF download.")

    today = date.today()
    col_y, col_m, col_p = st.columns([1.5, 2, 2.5])
    with col_y:
        selected_year = st.selectbox("Select Year", [today.year, today.year - 1], index=0)
    with col_m:
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        selected_month = st.selectbox("Select Month", range(1, 13), index=today.month - 1, format_func=lambda m: month_names[m - 1])
    with col_p:
        provider = st.selectbox(
            "AI Model for Report Narrative",
            ["local_flan", "local_grounded", "gemini", "openai"],
            format_func=lambda x: {
                "local_flan": "Local HuggingFace Transformer (FLAN-T5)",
                "local_grounded": "Grounded Contextual Engine (Instant)",
                "gemini": "Google Gemini API",
                "openai": "OpenAI GPT"
            }.get(x, x)
        )

    if st.button("📄 Generate Monthly Report", type="primary", key="btn_gen_report"):
        with st.spinner("Compiling monthly financial statements and running AI analysis..."):
            report_data = ReportService.generate_report_data(selected_year, selected_month, provider_name=provider)
            st.session_state.current_report = report_data
            
            # Generate PDF artifact
            pdf_path = ReportService.export_pdf_report(report_data)
            st.session_state.current_pdf_path = pdf_path

    st.markdown("---")

    if "current_report" in st.session_state and st.session_state.current_report:
        rep = st.session_state.current_report
        st.markdown(f"### 📋 Report: **{rep['month_label']}**")

        # PDF Download Button
        if "current_pdf_path" in st.session_state and Path(st.session_state.current_pdf_path).exists():
            with open(st.session_state.current_pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Download Formal PDF Report",
                data=pdf_bytes,
                file_name=Path(st.session_state.current_pdf_path).name,
                mime="application/pdf",
                type="primary"
            )

        st.markdown("---")

        # Section 1: Overview
        st.markdown("#### 1. Executive Expense Overview")
        ov = rep["overview"]
        o1, o2, o3, o4 = st.columns(4)
        o1.metric("Total Spending", f"₹{ov['total_spending']:,.2f}")
        o2.metric("Total Transactions", str(ov["transaction_count"]))
        o3.metric("Average / Transaction", f"₹{ov['average_expense']:,.2f}")
        o4.metric("Highest Single Expense", f"₹{ov['highest_expense']:,.2f}")

        # Section 2: Category Breakdown
        st.markdown("#### 2. Category Analysis")
        cats = rep["category_analysis"]
        if cats:
            st.dataframe(pd.DataFrame(cats), use_container_width=True, hide_index=True)
        else:
            st.info("No category expenses recorded for this month.")

        # Section 3: Spending Trends
        st.markdown("#### 3. Period-over-Period Trends")
        trends = rep["trends"]
        t_delta = trends["delta_spending"]
        dir_arrow = "🔺" if t_delta > 0 else "🔻"
        st.write(
            f"Previous Month Spending: **₹{trends['previous_month_total']:,.2f}** | "
            f"Net Variance: {dir_arrow} **₹{abs(t_delta):,.2f}** ({trends['pct_change']}% change)"
        )

        # Section 4: Generative AI Insights
        st.markdown(f"#### 4. Generative AI Financial Synthesis *(Engine: {rep['provider_used']})*")
        with st.container(border=True):
            st.markdown("##### Executive Summary")
            st.write(rep["ai_summary"])
            st.markdown("##### Key Spending Insights")
            st.markdown(rep["ai_insights"])
            st.markdown("##### Behavioral Patterns")
            st.markdown(rep["ai_patterns"])

        # Section 5: Optimization Suggestions
        st.markdown("#### 5. Practical Optimization Suggestions")
        with st.container(border=True):
            st.markdown(rep["suggestions"])

        st.warning(f"⚖️ **Disclaimer:** {rep['disclaimer']}")
    else:
        st.info("Click 'Generate Monthly Report' to compile your monthly financial statement and PDF.")
