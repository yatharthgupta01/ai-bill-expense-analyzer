"""
Budget Management View: Set and track overall and category-specific monthly spending limits.
"""
import streamlit as st
import pandas as pd
from datetime import date

from app.database.repository import BudgetRepository
from app.services.categorization import STANDARD_CATEGORIES
from app.utils.helpers import get_month_key

def render_budget():
    """Render budget configuration and progress tracking."""
    st.markdown("## 🎯 Monthly Budget Tracker")
    st.caption("Set spending targets, track utilization, and receive automatic warning alerts as you near budget thresholds.")

    # Select Month
    today = date.today()
    col_m1, col_m2 = st.columns([2, 4])
    with col_m1:
        current_year = today.year
        selected_year = st.selectbox("Year", [current_year, current_year - 1], index=0)
    with col_m2:
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        selected_month_idx = st.selectbox("Month", range(1, 13), index=today.month - 1, format_func=lambda m: month_names[m - 1])

    month_key = f"{selected_year}-{selected_month_idx:02d}"
    status = BudgetRepository.get_budget_status(month_key)

    tab_overview, tab_configure = st.tabs(["📊 Budget Utilization & Alerts", "⚙️ Configure Budgets"])

    with tab_overview:
        overall = status["overall"]
        st.markdown(f"### Overall Budget for **{month_names[selected_month_idx - 1]} {selected_year}**")

        if overall["budget"] > 0:
            b_col1, b_col2, b_col3, b_col4 = st.columns(4)
            with b_col1:
                st.metric("Total Budget", f"₹{overall['budget']:,.2f}")
            with b_col2:
                st.metric("Total Spent", f"₹{overall['spent']:,.2f}")
            with b_col3:
                st.metric("Remaining", f"₹{overall['remaining']:,.2f}")
            with b_col4:
                st.metric("Used (%)", f"{overall['percentage']}%")

            # Progress Bar & Alerts
            pct_norm = min(1.0, overall["percentage"] / 100.0)
            if overall["is_exceeded"]:
                st.error(f"🚨 **Budget Exceeded!** You have spent {overall['percentage']}% of your monthly allocation.")
                st.progress(1.0)
            elif overall["is_warning"]:
                st.warning(f"⚠️ **Caution:** You have utilized {overall['percentage']}% of your total budget.")
                st.progress(pct_norm)
            else:
                st.success(f"✅ On track! {overall['percentage']}% of total monthly budget used.")
                st.progress(pct_norm)
        else:
            st.info("No overall budget set for this month yet. Configure one in the 'Configure Budgets' tab.")

        st.markdown("---")

        # Category Budgets Table / Cards
        st.markdown("### 🏷️ Category Budget Status")
        categories = status["categories"]
        if categories:
            for cat in categories:
                c_box = st.container(border=True)
                with c_box:
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    c1.markdown(f"**{cat['category']}**")
                    c2.write(f"Spent: **₹{cat['spent']:,.2f}** / ₹{cat['budget']:,.2f}")
                    c3.write(f"Remaining: **₹{cat['remaining']:,.2f}**")
                    
                    if cat["budget"] > 0:
                        c4.write(f"**{cat['percentage']}%**")
                        prog = min(1.0, cat["percentage"] / 100.0)
                        if cat["is_exceeded"]:
                            st.error(f"🚨 **Alert:** {cat['category']} budget exceeded by ₹{abs(cat['spent'] - cat['budget']):,.2f}!")
                            st.progress(1.0)
                        elif cat["is_warning"]:
                            st.warning(f"⚠️ **Warning:** You have used {cat['percentage']}% of your {cat['category']} budget.")
                            st.progress(prog)
                        else:
                            st.progress(prog)
                    else:
                        c4.write("No budget set")
        else:
            st.info("No category expenses or budgets recorded for this month.")

    with tab_configure:
        st.markdown(f"### ⚙️ Set or Update Budgets for **{month_names[selected_month_idx - 1]} {selected_year}**")

        with st.form("set_overall_budget_form"):
            st.markdown("##### 1. Overall Monthly Limit")
            current_overall = status["overall"]["budget"]
            new_overall = st.number_input("Overall Monthly Budget (₹)", min_value=0.0, value=float(current_overall), step=1000.0)
            submit_overall = st.form_submit_button("💾 Save Overall Budget", type="primary")

            if submit_overall:
                BudgetRepository.set_budget(month_key, new_overall, category=None)
                st.success(f"Overall budget of ₹{new_overall:,.2f} saved for {month_key}!")
                st.rerun()

        st.markdown("---")

        with st.form("set_category_budget_form"):
            st.markdown("##### 2. Category-Specific Limits")
            cat_list = list(STANDARD_CATEGORIES.keys())
            target_cat = st.selectbox("Category", cat_list)
            
            # Find current budget for category
            curr_cat_obj = next((c for c in status["categories"] if c["category"] == target_cat), None)
            curr_cat_val = curr_cat_obj["budget"] if curr_cat_obj else 0.0

            new_cat_amt = st.number_input(f"Monthly Budget for {target_cat} (₹)", min_value=0.0, value=float(curr_cat_val), step=500.0)
            submit_cat = st.form_submit_button("💾 Save Category Budget")

            if submit_cat:
                BudgetRepository.set_budget(month_key, new_cat_amt, category=target_cat)
                st.success(f"Budget of ₹{new_cat_amt:,.2f} saved for {target_cat} in {month_key}!")
                st.rerun()
