"""
Visual Analytics Deep-Dive: Category Trends, Merchant Concentration, and Behavioral Patterns.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date

from app.database.repository import ExpenseRepository
from app.utils.helpers import get_date_range_preset

def render_analytics():
    """Render comprehensive visual analytics."""
    st.markdown("## 📈 Deep-Dive Visual Analytics")
    st.caption("Explore spending patterns, merchant concentrations, weekday vs weekend distributions, and category breakdowns.")

    # Time frame selector
    col_t1, col_t2 = st.columns([2, 4])
    with col_t1:
        time_preset = st.selectbox(
            "Analysis Period",
            ["This Month", "Last 3 Months", "Previous Month", "Today", "This Week"],
            index=0
        )
    start_date, end_date = get_date_range_preset(time_preset)
    with col_t2:
        st.info(f"Viewing analytics from **{start_date.strftime('%d %B %Y')}** to **{end_date.strftime('%d %B %Y')}**")

    # Fetch data
    categories = ExpenseRepository.get_category_breakdown(start_date, end_date)
    daily_trend = ExpenseRepository.get_daily_trend(start_date, end_date)
    merchants = ExpenseRepository.get_merchant_breakdown(start_date, end_date, limit=10)
    dow = ExpenseRepository.get_day_of_week_breakdown(start_date, end_date)

    if not categories:
        st.info("No expense data found for the selected timeframe. Please upload bills or seed sample data.")
        return

    # Tabs for analytics categories
    tab_overview, tab_behavior, tab_merchants = st.tabs([
        "📊 Spending & Category Breakdown",
        "📅 Temporal & Behavioral Trends",
        "🏪 Top Merchants & Vendors"
    ])

    with tab_overview:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 🍩 Category Share & Percentage")
            df_cat = pd.DataFrame(categories)
            fig_donut = px.pie(
                df_cat,
                values="total",
                names="category",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_donut.update_traces(textposition='inside', textinfo='percent+label')
            fig_donut.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False, height=350)
            st.plotly_chart(fig_donut, use_container_width=True)

        with c2:
            st.markdown("##### ⚖️ Total Spending by Category")
            fig_bar = px.bar(
                df_cat.sort_values(by="total", ascending=True),
                x="total",
                y="category",
                orientation='h',
                text="total",
                color="category",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_bar.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
            fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False, height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("##### 📋 Category Summary Table")
        st.dataframe(
            df_cat.rename(columns={
                "category": "Category",
                "total": "Total Amount (₹)",
                "count": "Transactions",
                "percentage": "Share (%)"
            }),
            use_container_width=True,
            hide_index=True
        )

    with tab_behavior:
        b1, b2 = st.columns(2)
        with b1:
            st.markdown("##### 🗓️ Weekday vs Weekend Expenditure")
            dow_data = [
                {"Period": "Weekday (Mon-Fri)", "Total": dow.get("weekday_total", 0.0)},
                {"Period": "Weekend (Sat-Sun)", "Total": dow.get("weekend_total", 0.0)}
            ]
            df_dow_summary = pd.DataFrame(dow_data)
            fig_dow = px.pie(
                df_dow_summary,
                values="Total",
                names="Period",
                hole=0.4,
                color="Period",
                color_discrete_map={"Weekday (Mon-Fri)": "#3b82f6", "Weekend (Sat-Sun)": "#f59e0b"}
            )
            fig_dow.update_traces(textinfo='percent+label')
            fig_dow.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig_dow, use_container_width=True)

        with b2:
            st.markdown("##### 📅 Daily Day-of-Week Distribution")
            day_totals = dow.get("day_totals", {})
            df_days = pd.DataFrame([
                {"Day": day, "Spending": tot}
                for day, tot in day_totals.items()
            ])
            fig_days = px.bar(
                df_days,
                x="Day",
                y="Spending",
                text="Spending",
                color="Day",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig_days.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
            fig_days.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False, height=320)
            st.plotly_chart(fig_days, use_container_width=True)

        st.markdown("##### 📈 Daily Spending Cumulative Curve")
        df_daily = pd.DataFrame(daily_trend)
        if not df_daily.empty:
            df_daily["cumulative"] = df_daily["total"].cumsum()
            fig_cum = px.area(
                df_daily,
                x="date",
                y="cumulative",
                labels={"date": "Date", "cumulative": "Cumulative Spend (₹)"},
                color_discrete_sequence=["#6366f1"]
            )
            fig_cum.update_layout(margin=dict(t=20, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_cum, use_container_width=True)

    with tab_merchants:
        st.markdown("##### 🏪 Top 10 Merchants by Total Spend")
        df_merchants = pd.DataFrame(merchants)
        if not df_merchants.empty:
            fig_m = px.bar(
                df_merchants.sort_values(by="total", ascending=True),
                x="total",
                y="merchant",
                orientation='h',
                text="total",
                labels={"total": "Total Spent (₹)", "merchant": "Merchant / Vendor"},
                color="total",
                color_continuous_scale="Blues"
            )
            fig_m.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
            fig_m.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=400)
            st.plotly_chart(fig_m, use_container_width=True)
        else:
            st.write("No merchant records available.")
