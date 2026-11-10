"""
Streamlit Dashboard View: Executive KPIs, Budget Warnings, and Interactive Charts.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date

from app.database.repository import ExpenseRepository, BudgetRepository
from app.utils.helpers import get_date_range_preset, format_currency, get_month_key

def render_dashboard():
    """Render the main executive overview dashboard."""
    st.markdown("## 📊 Expense Analytics Dashboard")
    st.caption("Real-time personal spending overview, key metrics, and visual analytics.")

    # Top Control Bar: Date Range Filter
    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 2])
    with col_filter1:
        preset = st.selectbox(
            "Filter Period",
            ["This Month", "Today", "This Week", "Previous Month", "Last 3 Months", "Custom Range"],
            index=0
        )

    start_date = None
    end_date = None

    if preset == "Custom Range":
        with col_filter2:
            start_date = st.date_input("Start Date", value=date.today().replace(day=1))
        with col_filter3:
            end_date = st.date_input("End Date", value=date.today())
    else:
        start_date, end_date = get_date_range_preset(preset)
        with col_filter2:
            st.info(f"📅 Active Range: **{start_date.strftime('%d %b %Y')}** to **{end_date.strftime('%d %b %Y')}**")

    # Fetch stats
    stats = ExpenseRepository.get_summary_stats(start_date, end_date)
    cat_breakdown = ExpenseRepository.get_category_breakdown(start_date, end_date)

    # Check Budget Warnings for current month
    curr_month_key = get_month_key(date.today())
    budget_status = BudgetRepository.get_budget_status(curr_month_key)
    overall_b = budget_status["overall"]

    if overall_b["is_exceeded"]:
        st.error(
            f"🚨 **Monthly Budget Exceeded!** You have spent **₹{overall_b['spent']:,.2f}** "
            f"out of your monthly budget of **₹{overall_b['budget']:,.2f}** ({overall_b['percentage']}%)."
        )
    elif overall_b["is_warning"]:
        st.warning(
            f"⚠️ **Budget Alert:** You have used **{overall_b['percentage']}%** "
            f"of your total monthly budget (₹{overall_b['spent']:,.2f} / ₹{overall_b['budget']:,.2f})."
        )

    # Check category budget warnings
    for cat_b in budget_status["categories"]:
        if cat_b["is_exceeded"]:
            st.error(f"🚨 **{cat_b['category']} Budget Exceeded:** Spent ₹{cat_b['spent']:,.2f} / ₹{cat_b['budget']:,.2f} ({cat_b['percentage']}%)")
        elif cat_b["is_warning"]:
            st.warning(f"⚠️ **{cat_b['category']} Budget Warning:** You have used {cat_b['percentage']}% of your {cat_b['category']} budget.")

    st.markdown("---")

    # Metric KPI Cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Total Expenses", f"₹{stats['total_spending']:,.2f}")
    with kpi2:
        st.metric("Transactions", f"{stats['transaction_count']}")
    with kpi3:
        st.metric("Average / Txn", f"₹{stats['average_expense']:,.2f}")
    with kpi4:
        st.metric("Highest Expense", f"₹{stats['highest_expense']:,.2f}")
    with kpi5:
        top_cat_label = f"{stats['top_category']}" if stats['top_category'] != "None" else "N/A"
        st.metric("Top Category", top_cat_label)

    st.markdown("---")

    if stats["transaction_count"] == 0:
        st.info("ℹ️ No transactions found for the selected period. Upload bills in the **Upload Bill** tab or seed sample data.")
        return

    # Visual Analytics: 4 Charts Layout
    row1_col1, row1_col2 = st.columns(2)

    # 1. Category Distribution (Donut Chart)
    with row1_col1:
        st.markdown("##### 🍩 Category Distribution")
        df_cat = pd.DataFrame(cat_breakdown)
        if not df_cat.empty:
            fig_pie = px.pie(
                df_cat,
                values="total",
                names="category",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False, height=320)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("No category data available.")

    # 2. Monthly Spending (Bar Chart)
    with row1_col2:
        st.markdown("##### 📊 Monthly Spending")
        monthly_data = ExpenseRepository.get_monthly_spending(months_back=6)
        df_month = pd.DataFrame(monthly_data)
        if not df_month.empty:
            fig_bar = px.bar(
                df_month,
                x="month",
                y="total",
                text="total",
                labels={"month": "Month", "total": "Total Spent (₹)"},
                color_discrete_sequence=["#3b82f6"]
            )
            fig_bar.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
            fig_bar.update_layout(margin=dict(t=20, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.write("No monthly history available.")

    row2_col1, row2_col2 = st.columns(2)

    # 3. Spending Trend (Line Chart)
    with row2_col1:
        st.markdown("##### 📈 Daily Spending Trend")
        daily_data = ExpenseRepository.get_daily_trend(start_date, end_date)
        df_daily = pd.DataFrame(daily_data)
        if not df_daily.empty and len(df_daily) > 1:
            fig_line = px.line(
                df_daily,
                x="date",
                y="total",
                markers=True,
                labels={"date": "Date", "total": "Daily Total (₹)"},
                color_discrete_sequence=["#10b981"]
            )
            fig_line.update_layout(margin=dict(t=20, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Record more transactions across multiple dates to view the trendline.")

    # 4. Category Comparison (Horizontal Bar Chart)
    with row2_col2:
        st.markdown("##### ⚖️ Category Comparison")
        if not df_cat.empty:
            df_cat_sorted = df_cat.sort_values(by="total", ascending=True)
            fig_cat_bar = px.bar(
                df_cat_sorted,
                x="total",
                y="category",
                orientation='h',
                text="total",
                labels={"total": "Total Amount (₹)", "category": "Category"},
                color="category",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_cat_bar.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
            fig_cat_bar.update_layout(margin=dict(t=20, b=10, l=10, r=10), showlegend=False, height=320)
            st.plotly_chart(fig_cat_bar, use_container_width=True)
        else:
            st.write("No comparison data available.")

    st.markdown("---")

    # Recent Transactions Snippet
    st.markdown("##### 🕒 Recent Transactions")
    recent = ExpenseRepository.list_expenses(limit=5)
    if recent:
        recent_data = [
            {
                "Date": exp.date.strftime("%d %b %Y") if exp.date else "-",
                "Merchant": exp.merchant,
                "Category": exp.category,
                "Payment": exp.payment_method,
                "Total Amount": f"₹{exp.total:,.2f}"
            }
            for exp in recent
        ]
        st.dataframe(pd.DataFrame(recent_data), use_container_width=True, hide_index=True)
