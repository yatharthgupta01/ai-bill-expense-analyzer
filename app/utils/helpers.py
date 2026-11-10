"""
Utility helpers for date processing, formatting, and mathematical consistency.
"""
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import re

def clean_amount(val_str: Optional[str]) -> float:
    """Clean and parse a string representing a monetary amount into a float."""
    if not val_str:
        return 0.0
    if isinstance(val_str, (int, float)):
        return float(val_str)
    
    cleaned = str(val_str).strip()
    # Remove currency symbols (₹, $, €, £, Rs., INR) and unwanted characters
    cleaned = re.sub(r"[₹\$€£]|Rs\.?|INR", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace(",", "").strip()
    
    # Match decimal or integer numbers
    match = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0

def format_currency(amount: float, currency: str = "₹") -> str:
    """Format an amount into a standard currency string (e.g. ₹1,250.50)."""
    if amount is None:
        amount = 0.0
    return f"{currency}{amount:,.2f}"

def parse_date_string(date_str: Optional[str]) -> Optional[date]:
    """
    Robustly parse date strings from OCR text into a datetime.date object.
    Supports formats: DD/MM/YYYY, YYYY-MM-DD, MM/DD/YYYY, DD-MMM-YYYY, etc.
    """
    if not date_str or not str(date_str).strip():
        return None
    
    cleaned = str(date_str).strip()
    # Replace separators like '.', '-', '/' with standard '/'
    cleaned = re.sub(r"[\s\.\-]+", "/", cleaned)
    
    date_formats = [
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d/%b/%Y",
        "%d/%B/%Y",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%m/%d/%y",
        "%b/%d/%Y",
        "%B/%d/%Y",
    ]
    
    for fmt in date_formats:
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
            # Sanity check: year must be reasonable (e.g. between 2000 and 2040)
            if 2000 <= parsed.year <= 2040:
                return parsed
        except (ValueError, TypeError):
            continue
            
    # Try finding date pattern within text
    patterns = [
        r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",  # YYYY-MM-DD
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",  # DD-MM-YYYY or MM-DD-YYYY
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{2})",   # DD-MM-YY
    ]
    for pat in patterns:
        m = re.search(pat, cleaned)
        if m:
            parts = [int(p) for p in m.groups()]
            if len(parts) == 3:
                try:
                    if parts[0] > 1900:  # YYYY-MM-DD
                        return date(parts[0], parts[1], parts[2])
                    else:
                        # Assume DD/MM/YYYY or MM/DD/YYYY
                        day, month, year = parts[0], parts[1], parts[2]
                        if year < 100:
                            year += 2000
                        if month > 12 >= day:
                            day, month = month, day
                        if 1 <= month <= 12 and 1 <= day <= 31:
                            return date(year, month, day)
                except ValueError:
                    pass

    return None

def get_date_range_preset(preset: str, ref_date: Optional[date] = None) -> Tuple[date, date]:
    """
    Get (start_date, end_date) for standard filtering presets:
    - Today
    - This week
    - This month
    - Previous month
    - Last 3 months
    """
    ref = ref_date or date.today()
    
    preset_lower = preset.lower().strip()
    
    if preset_lower == "today":
        return ref, ref
        
    elif preset_lower in ["this week", "week"]:
        start = ref - timedelta(days=ref.weekday())  # Monday
        end = start + timedelta(days=6)
        return start, end
        
    elif preset_lower in ["this month", "month"]:
        start = date(ref.year, ref.month, 1)
        # End of current month
        next_month = ref.month + 1 if ref.month < 12 else 1
        next_year = ref.year if ref.month < 12 else ref.year + 1
        end = date(next_year, next_month, 1) - timedelta(days=1)
        return start, end
        
    elif preset_lower in ["previous month", "last month"]:
        prev_month = ref.month - 1 if ref.month > 1 else 12
        prev_year = ref.year if ref.month > 1 else ref.year - 1
        start = date(prev_year, prev_month, 1)
        end = date(ref.year, ref.month, 1) - timedelta(days=1)
        return start, end
        
    elif preset_lower in ["last 3 months", "3 months"]:
        end = ref
        start = (ref.replace(day=1) - timedelta(days=60)).replace(day=1)
        return start, end
        
    # Default to this month
    start = date(ref.year, ref.month, 1)
    end = ref
    return start, end

def get_month_key(d: date) -> str:
    """Format a date into a month key 'YYYY-MM'."""
    return d.strftime("%Y-%m")
