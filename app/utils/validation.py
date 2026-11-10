"""
Validation logic for expense data and financial arithmetic consistency.
"""
from typing import Dict, Any, List, Tuple
from datetime import date

def validate_expense_data(data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate expense data fields and verify mathematical consistency:
    Subtotal + Tax + Additional Charges - Discount ≈ Total
    
    Returns:
        (is_valid, warnings, errors)
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    merchant = str(data.get("merchant", "")).strip()
    if not merchant:
        errors.append("Merchant / Vendor name cannot be empty.")
        
    expense_date = data.get("date")
    if not expense_date:
        errors.append("Expense date is required.")
    elif isinstance(expense_date, str):
        errors.append("Expense date must be a valid date object.")
        
    try:
        total = float(data.get("total", 0.0) or 0.0)
    except (ValueError, TypeError):
        total = 0.0
        errors.append("Total amount must be a numeric value.")
        
    if total < 0:
        errors.append("Total amount cannot be negative.")
    elif total == 0.0:
        warnings.append("Total amount is zero. Please verify the bill total.")
        
    # Check arithmetic breakdown
    subtotal = float(data.get("subtotal", 0.0) or 0.0)
    tax = float(data.get("tax", 0.0) or 0.0)
    discount = float(data.get("discount", 0.0) or 0.0)
    additional_charges = float(data.get("additional_charges", 0.0) or 0.0)
    
    # If subtotal is 0 but we have total, estimate subtotal
    if subtotal == 0.0 and total > 0:
        calculated_subtotal = max(0.0, total - tax - additional_charges + discount)
        data["subtotal"] = round(calculated_subtotal, 2)
        subtotal = data["subtotal"]
    
    # Verify mathematical balance if components exist
    if subtotal > 0 and (tax > 0 or discount > 0 or additional_charges > 0):
        expected_total = subtotal + tax + additional_charges - discount
        diff = abs(expected_total - total)
        if diff > 1.0:
            warnings.append(
                f"Arithmetic discrepancy detected: Subtotal ({subtotal:.2f}) + Tax ({tax:.2f}) "
                f"+ Charges ({additional_charges:.2f}) - Discount ({discount:.2f}) = {expected_total:.2f}, "
                f"which differs from Total ({total:.2f}) by {diff:.2f}."
            )
            
    # Items validation
    items = data.get("items", [])
    if items and isinstance(items, list):
        items_sum = 0.0
        for idx, item in enumerate(items, 1):
            name = item.get("item_name", "").strip()
            qty = float(item.get("quantity", 1.0) or 1.0)
            price = float(item.get("unit_price", 0.0) or 0.0)
            item_tot = float(item.get("total_price", 0.0) or 0.0)
            
            if not name:
                warnings.append(f"Line item #{idx} is missing a name.")
            if item_tot == 0.0 and price > 0:
                item["total_price"] = round(qty * price, 2)
                item_tot = item["total_price"]
            items_sum += item_tot
            
        if items_sum > 0 and subtotal > 0:
            item_diff = abs(items_sum - subtotal)
            if item_diff > 2.0 and abs(items_sum - total) > 2.0:
                warnings.append(
                    f"Sum of itemized prices ({items_sum:.2f}) differs from subtotal ({subtotal:.2f})."
                )

    is_valid = len(errors) == 0
    return is_valid, warnings, errors
