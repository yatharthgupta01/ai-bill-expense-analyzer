"""
Expenses Management View: Search, Filter, Itemized Inspection, Edit, and Delete.
"""
import streamlit as st
import pandas as pd
from datetime import date

from app.database.repository import ExpenseRepository
from app.services.expense_service import ExpenseService
from app.services.categorization import STANDARD_CATEGORIES

CATEGORIES_FILTER = ["All"] + list(STANDARD_CATEGORIES.keys())
PAYMENT_FILTER = ["All", "Cash", "UPI", "Credit Card", "Debit Card", "Net Banking"]

def render_expenses():
    """Render the expenses list, search filters, and action dialogs."""
    st.markdown("## 📋 Manage Expenses")
    st.caption("Search, filter, inspect receipt line items, edit, and organize all stored transactions.")

    # Search & Filter Toolbar
    with st.expander("🔍 Search & Filter Tools", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 1, 1])
        with f_col1:
            search_query = st.text_input("Search Merchant, Category, or Invoice #", placeholder="e.g. Amazon, Starbucks, Groceries...")
        with f_col2:
            selected_cat = st.selectbox("Category", CATEGORIES_FILTER, index=0)
        with f_col3:
            selected_pay = st.selectbox("Payment Method", PAYMENT_FILTER, index=0)
        with f_col4:
            sort_order = st.selectbox(
                "Sort By",
                [("date_desc", "Date (Newest First)"), ("date_asc", "Date (Oldest First)"), ("total_desc", "Amount (High to Low)"), ("total_asc", "Amount (Low to High)")],
                format_func=lambda x: x[1]
            )

        amt_col1, amt_col2 = st.columns(2)
        with amt_col1:
            min_amt = st.number_input("Min Amount (₹)", min_value=0.0, value=0.0, step=50.0)
        with amt_col2:
            max_amt = st.number_input("Max Amount (₹, 0 for no limit)", min_value=0.0, value=0.0, step=500.0)

    # Query expenses
    expenses = ExpenseRepository.list_expenses(
        category=selected_cat if selected_cat != "All" else None,
        payment_method=selected_pay if selected_pay != "All" else None,
        search=search_query if search_query.strip() else None,
        min_amount=min_amt if min_amt > 0 else None,
        max_amount=max_amt if max_amt > 0 else None,
        order_by=sort_order[0]
    )

    st.markdown(f"**Found {len(expenses)} expense transaction(s):**")

    if not expenses:
        st.info("No matching expenses found. Try adjusting your search filters or upload a new bill.")
        return

    # Selected expense state for Details / Edit / Delete
    if "selected_expense_id" not in st.session_state:
        st.session_state.selected_expense_id = None
    if "action_mode" not in st.session_state:
        st.session_state.action_mode = None  # "view", "edit", "delete"

    # Action Confirmation Dialogs
    if st.session_state.action_mode == "view" and st.session_state.selected_expense_id:
        exp = ExpenseRepository.get_expense_by_id(st.session_state.selected_expense_id)
        if exp:
            with st.container(border=True):
                st.markdown(f"### 🧾 Expense Receipt #{exp.id}: **{exp.merchant}**")
                v_col1, v_col2 = st.columns(2)
                with v_col1:
                    st.write(f"📅 **Date:** {exp.date.strftime('%d %B %Y')}")
                    st.write(f"🏷️ **Category:** {exp.category}")
                    st.write(f"💳 **Payment Method:** {exp.payment_method}")
                    if exp.invoice_number:
                        st.write(f"🔖 **Invoice #:** {exp.invoice_number}")
                    if exp.source_file:
                        st.write(f"📎 **Attached File:** `{exp.source_file}`")
                with v_col2:
                    st.write(f"💵 **Subtotal:** ₹{exp.subtotal:,.2f}")
                    st.write(f"🏛️ **Tax / GST:** ₹{exp.tax:,.2f}")
                    st.write(f"🎁 **Discount:** ₹{exp.discount:,.2f}")
                    st.write(f"📦 **Additional Charges:** ₹{exp.additional_charges:,.2f}")
                    st.markdown(f"#### 💰 **Final Total: ₹{exp.total:,.2f}**")

                if exp.notes:
                    st.info(f"📝 **Notes:** {exp.notes}")

                # Line Items Table
                st.markdown("##### 🛒 Itemized Breakdown")
                if exp.items:
                    items_data = [
                        {
                            "Item Name": item.item_name,
                            "Quantity": item.quantity,
                            "Unit Price": f"₹{item.unit_price:,.2f}",
                            "Total Price": f"₹{item.total_price:,.2f}"
                        }
                        for item in exp.items
                    ]
                    st.dataframe(pd.DataFrame(items_data), use_container_width=True, hide_index=True)
                else:
                    st.caption("No individual line items recorded for this expense.")

                if st.button("Close Receipt Details"):
                    st.session_state.action_mode = None
                    st.session_state.selected_expense_id = None
                    st.rerun()

    # Edit Mode
    elif st.session_state.action_mode == "edit" and st.session_state.selected_expense_id:
        exp = ExpenseRepository.get_expense_by_id(st.session_state.selected_expense_id)
        if exp:
            with st.container(border=True):
                st.markdown(f"### ✏️ Edit Expense #{exp.id}: **{exp.merchant}**")
                with st.form("edit_expense_form"):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        e_merchant = st.text_input("Merchant", value=exp.merchant)
                        e_date = st.date_input("Date", value=exp.date)
                        cat_list = list(STANDARD_CATEGORIES.keys())
                        c_idx = cat_list.index(exp.category) if exp.category in cat_list else 0
                        e_category = st.selectbox("Category", cat_list, index=c_idx)
                        p_list = ["Cash", "UPI", "Credit Card", "Debit Card", "Net Banking"]
                        p_idx = p_list.index(exp.payment_method) if exp.payment_method in p_list else 0
                        e_pay = st.selectbox("Payment Method", p_list, index=p_idx)
                    with e_col2:
                        e_inv = st.text_input("Invoice #", value=exp.invoice_number or "")
                        e_subtotal = st.number_input("Subtotal (₹)", value=float(exp.subtotal), step=10.0)
                        e_tax = st.number_input("Tax (₹)", value=float(exp.tax), step=5.0)
                        e_total = st.number_input("Total Amount (₹)", value=float(exp.total), step=10.0)

                    e_notes = st.text_area("Notes", value=exp.notes or "")

                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        save_edit = st.form_submit_button("💾 Save Changes", type="primary")
                    with btn_c2:
                        cancel_edit = st.form_submit_button("❌ Cancel")

                    if cancel_edit:
                        st.session_state.action_mode = None
                        st.session_state.selected_expense_id = None
                        st.rerun()

                    if save_edit:
                        ExpenseRepository.update_expense(
                            exp.id,
                            {
                                "merchant": e_merchant,
                                "date": e_date,
                                "category": e_category,
                                "payment_method": e_pay,
                                "invoice_number": e_inv,
                                "subtotal": e_subtotal,
                                "tax": e_tax,
                                "total": e_total,
                                "notes": e_notes
                            }
                        )
                        st.success("Expense successfully updated!")
                        st.session_state.action_mode = None
                        st.session_state.selected_expense_id = None
                        st.rerun()

    # Delete Confirmation Dialog
    elif st.session_state.action_mode == "delete" and st.session_state.selected_expense_id:
        exp = ExpenseRepository.get_expense_by_id(st.session_state.selected_expense_id)
        if exp:
            st.error(f"⚠️ **Are you sure you want to permanently delete expense #{exp.id} ({exp.merchant} - ₹{exp.total:,.2f})?**")
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                if st.button("🗑️ Yes, Delete Expense", type="primary"):
                    ExpenseRepository.delete_expense(exp.id)
                    st.success("Expense deleted successfully.")
                    st.session_state.action_mode = None
                    st.session_state.selected_expense_id = None
                    st.rerun()
            with d_col2:
                if st.button("Cancel"):
                    st.session_state.action_mode = None
                    st.session_state.selected_expense_id = None
                    st.rerun()

    # Expense Table with Action Buttons
    st.markdown("---")
    header_cols = st.columns([1.5, 2.5, 1.8, 1.8, 1.8, 2.2])
    header_cols[0].markdown("**Date**")
    header_cols[1].markdown("**Merchant**")
    header_cols[2].markdown("**Category**")
    header_cols[3].markdown("**Amount**")
    header_cols[4].markdown("**Payment**")
    header_cols[5].markdown("**Actions**")

    for exp in expenses:
        cols = st.columns([1.5, 2.5, 1.8, 1.8, 1.8, 2.2])
        cols[0].write(exp.date.strftime("%d-%b-%Y") if exp.date else "-")
        cols[1].write(f"**{exp.merchant}**")
        cols[2].write(exp.category)
        cols[3].write(f"**₹{exp.total:,.2f}**")
        cols[4].write(exp.payment_method or "Cash")

        btn_c1, btn_c2, btn_c3 = cols[5].columns(3)
        with btn_c1:
            if st.button("👁️", key=f"view_{exp.id}", help="View Details"):
                st.session_state.selected_expense_id = exp.id
                st.session_state.action_mode = "view"
                st.rerun()
        with btn_c2:
            if st.button("✏️", key=f"edit_{exp.id}", help="Edit Expense"):
                st.session_state.selected_expense_id = exp.id
                st.session_state.action_mode = "edit"
                st.rerun()
        with btn_c3:
            if st.button("🗑️", key=f"del_{exp.id}", help="Delete Expense"):
                st.session_state.selected_expense_id = exp.id
                st.session_state.action_mode = "delete"
                st.rerun()
