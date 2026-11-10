"""
Bill & Receipt Upload View: OCR Extraction and Interactive Review Screen.
"""
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
from PIL import Image
import io

from app.services.expense_service import ExpenseService
from app.services.categorization import STANDARD_CATEGORIES
from app.ocr.image_processor import is_tesseract_available

CATEGORIES_LIST = list(STANDARD_CATEGORIES.keys())
PAYMENT_METHODS = ["Cash", "UPI", "Credit Card", "Debit Card", "Net Banking"]

# Sample bill templates for instant testing & evaluation
SAMPLE_RECEIPTS = {
    "-- Select a sample bill to test --": "",
    "Starbucks Coffee & Snacks (Cafe Bill)": """STARBUCKS COFFEE INDIA
Connaught Place, New Delhi
GSTIN: 07AAAAC1234F1Z8
Date: 04/11/2026 Time: 16:35:10
Invoice No: SBX-94821

Items:
Caffe Latte 1 x 280.00 = 280.00
Blueberry Muffin 1 x 220.00 = 220.00
Cold Brew 2 x 310.00 = 620.00

Sub Total: 1120.00
CGST 2.5%: 28.00
SGST 2.5%: 28.00
Service Charge: 50.00
Discount: 100.00
Grand Total: 1126.00
Payment: UPI / GPay
Thank you for visiting!""",

    "FreshMart Supermarket (Grocery Receipt)": """FRESHMART RETAIL HYPERMARKET
Indiranagar, Bengaluru
Receipt No: FM-2026-88192
Date: 02/11/2026

Items:
Organic Whole Milk 2 x 65.00 = 130.00
Multigrain Bread 1 x 55.00 = 55.00
Fresh Apples 1kg 1 x 180.00 = 180.00
Almonds 500g 1 x 450.00 = 450.00
Basmati Rice 5kg 1 x 620.00 = 620.00

Subtotal: 1435.00
Discount: 85.00
Tax / GST: 45.00
Total Amount: 1395.00
Payment Method: Credit Card
Items count: 5""",

    "Shell Petroleum (Fuel & Transportation Bill)": """SHELL AUTOMOTIVE FUELS
Highway Station 12, Pune
Bill #: SHL-449102
Date: 05/11/2026

Power Petrol 35.5L 1 x 3727.50 = 3727.50

Subtotal: 3727.50
VAT / State Cess: 0.00
Total: 3727.50
Payment: Debit Card
Drive safe!""",

    "Apollo Pharmacy (Healthcare Invoice)": """APOLLO PHARMACIES LTD
Koramangala, Bengaluru
GSTIN: 29AABCA9999K1Z4
Tax Invoice No: APL-60021
Date: 06/11/2026

Paracetamol 650mg 2 x 30.00 = 60.00
Vitamin C Tablets 1 x 150.00 = 150.00
Cough Syrup 1 x 115.00 = 115.00

Sub Total: 325.00
GST: 18.00
Net Amount: 343.00
Payment: UPI / PhonePe"""
}

def render_upload():
    """Render the upload and review flow."""
    st.markdown("## 📄 Upload Bill / Receipt")
    st.caption("Upload receipt images (JPG, PNG) or invoices (PDF) for automated OCR and AI-assisted extraction.")

    # OCR Availability Banner
    tesseract_ok = is_tesseract_available()
    if not tesseract_ok:
        st.info(
            "💡 **Note on OCR:** Direct PDF text extraction is active. For scanned image OCR, ensure Tesseract-OCR is installed. "
            "You can test digital PDFs, paste/select sample bill text below, or enter values in the review screen."
        )

    # In-memory session state for draft
    if "current_draft" not in st.session_state:
        st.session_state.current_draft = None
    if "upload_success_message" not in st.session_state:
        st.session_state.upload_success_message = None

    if st.session_state.upload_success_message:
        st.success(st.session_state.upload_success_message)
        st.session_state.upload_success_message = None

    # Step 1: Input Options (File Upload or Sample Bill Selector)
    tab_file, tab_sample = st.tabs(["📁 Upload File (PDF / Image)", "⚡ Quick Sample Bill Demo"])

    uploaded_file = None
    with tab_file:
        uploaded_file = st.file_uploader(
            "Choose a bill, receipt, or invoice",
            type=["jpg", "jpeg", "png", "pdf"],
            help="Supported formats: JPG, JPEG, PNG, PDF."
        )
        if uploaded_file is not None:
            if st.button("🚀 Process Uploaded Document", key="btn_process_file", type="primary"):
                with st.spinner("Extracting and parsing document..."):
                    file_bytes = uploaded_file.read()
                    filename = uploaded_file.name
                    result = ExpenseService.process_document(file_bytes, filename)
                    if result["success"]:
                        st.session_state.current_draft = result["draft"]
                        st.session_state.uploaded_preview_bytes = file_bytes
                        st.session_state.uploaded_preview_name = filename
                        st.rerun()
                    else:
                        st.error(f"Extraction error: {result.get('error')}")

    with tab_sample:
        st.write("Test immediate extraction with realistic sample bills without uploading files:")
        sample_choice = st.selectbox("Select a sample receipt:", list(SAMPLE_RECEIPTS.keys()))
        if sample_choice and sample_choice != "-- Select a sample bill to test --":
            raw_sample_text = SAMPLE_RECEIPTS[sample_choice]
            st.text_area("Sample Bill Text:", raw_sample_text, height=180, disabled=True)
            if st.button("🚀 Extract from Sample Bill", key="btn_process_sample", type="primary"):
                with st.spinner("Parsing sample receipt..."):
                    from app.ocr.extractor import BillExtractor
                    draft = BillExtractor.extract(raw_sample_text, filename=f"sample_{sample_choice[:10]}.txt")
                    st.session_state.current_draft = draft
                    st.session_state.uploaded_preview_bytes = None
                    st.session_state.uploaded_preview_name = sample_choice
                    st.rerun()

    st.markdown("---")

    # Step 2: Review Screen (Section 6 requirement)
    draft = st.session_state.current_draft
    if draft is not None:
        st.markdown("### 📝 Review & Validate Extracted Data")
        st.caption("Verify and correct any extracted fields before saving to the database. Values marked in bold require attention.")

        # Show any warnings from extraction
        if draft.get("warnings"):
            for w in draft["warnings"]:
                st.warning(f"⚠️ {w}")

        # Review Form
        with st.form("expense_review_form"):
            col1, col2 = st.columns(2)
            with col1:
                merchant = st.text_input("Merchant / Vendor Name", value=draft.get("merchant", ""))
                invoice_no = st.text_input("Invoice / Bill #", value=draft.get("invoice_number") or "")
                
                exp_date_val = draft.get("date")
                if not isinstance(exp_date_val, date):
                    exp_date_val = date.today()
                exp_date = st.date_input("Transaction Date", value=exp_date_val)
                
                curr_cat = draft.get("category", "Other")
                cat_idx = CATEGORIES_LIST.index(curr_cat) if curr_cat in CATEGORIES_LIST else CATEGORIES_LIST.index("Other")
                category = st.selectbox("Expense Category (AI Suggested)", CATEGORIES_LIST, index=cat_idx)
                
                curr_pay = draft.get("payment_method", "Cash")
                pay_idx = PAYMENT_METHODS.index(curr_pay) if curr_pay in PAYMENT_METHODS else 0
                payment_method = st.selectbox("Payment Method", PAYMENT_METHODS, index=pay_idx)

            with col2:
                currency = st.text_input("Currency Symbol", value=draft.get("currency", "₹"), max_chars=3)
                subtotal = st.number_input("Subtotal", min_value=0.0, value=float(draft.get("subtotal", 0.0)), step=10.0, format="%.2f")
                tax = st.number_input("Tax / GST", min_value=0.0, value=float(draft.get("tax", 0.0)), step=5.0, format="%.2f")
                discount = st.number_input("Discount", min_value=0.0, value=float(draft.get("discount", 0.0)), step=5.0, format="%.2f")
                additional_charges = st.number_input("Service / Additional Charges", min_value=0.0, value=float(draft.get("additional_charges", 0.0)), step=5.0, format="%.2f")
                total = st.number_input("Final Total Amount", min_value=0.0, value=float(draft.get("total", 0.0)), step=10.0, format="%.2f")

            # Mathematical Balance Check
            calc_tot = round(subtotal + tax + additional_charges - discount, 2)
            diff = abs(calc_tot - total)
            if diff > 1.0:
                st.info(
                    f"💡 Calculated Total (Subtotal ₹{subtotal:.2f} + Tax ₹{tax:.2f} + Charges ₹{additional_charges:.2f} - Discount ₹{discount:.2f}) "
                    f"= **₹{calc_tot:.2f}**, which differs from Final Total (**₹{total:.2f}**)."
                )

            # Itemized breakdown review
            st.markdown("##### 🛒 Line Items Breakdown")
            items = draft.get("items", [])
            items_df = pd.DataFrame(items) if items else pd.DataFrame(columns=["item_name", "quantity", "unit_price", "total_price"])
            
            edited_items_df = st.data_editor(
                items_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "item_name": st.column_config.TextColumn("Item Description", required=True),
                    "quantity": st.column_config.NumberColumn("Qty", min_value=1.0, default=1.0, step=1.0),
                    "unit_price": st.column_config.NumberColumn("Unit Price (₹)", min_value=0.0, default=0.0, format="%.2f"),
                    "total_price": st.column_config.NumberColumn("Total Price (₹)", min_value=0.0, default=0.0, format="%.2f")
                }
            )

            notes = st.text_area("Optional Notes", value=draft.get("notes") or "", placeholder="e.g. Lunch with project team...")

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                save_submitted = st.form_submit_button("💾 Save Expense to Database", type="primary")
            with col_btn2:
                cancel_submitted = st.form_submit_button("❌ Discard / Cancel")

            if cancel_submitted:
                st.session_state.current_draft = None
                st.rerun()

            if save_submitted:
                # Prepare updated items list
                updated_items = []
                for _, row in edited_items_df.iterrows():
                    name = str(row.get("item_name", "")).strip()
                    if name:
                        qty = float(row.get("quantity", 1.0) or 1.0)
                        u_price = float(row.get("unit_price", 0.0) or 0.0)
                        t_price = float(row.get("total_price", 0.0) or (qty * u_price))
                        updated_items.append({
                            "item_name": name,
                            "quantity": qty,
                            "unit_price": u_price,
                            "total_price": t_price
                        })

                save_payload = {
                    "merchant": merchant,
                    "date": exp_date,
                    "invoice_number": invoice_no,
                    "category": category,
                    "payment_method": payment_method,
                    "currency": currency,
                    "subtotal": subtotal,
                    "tax": tax,
                    "discount": discount,
                    "additional_charges": additional_charges,
                    "total": total,
                    "notes": notes,
                    "source_file": draft.get("source_file"),
                    "items": updated_items
                }

                ok, saved_exp, warnings, errors = ExpenseService.save_reviewed_expense(save_payload)
                if ok:
                    st.session_state.current_draft = None
                    st.session_state.upload_success_message = f"✅ Expense from **{merchant}** for **₹{total:,.2f}** successfully saved!"
                    st.rerun()
                else:
                    for err in errors:
                        st.error(f"❌ {err}")
                    for w in warnings:
                        st.warning(f"⚠️ {w}")
