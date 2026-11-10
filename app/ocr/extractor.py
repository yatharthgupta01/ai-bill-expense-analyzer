"""
Structured information extraction engine for bills, receipts, and invoices.
"""
from typing import Dict, Any, List, Optional, Tuple
import re
from datetime import date, datetime
from app.utils.helpers import clean_amount, parse_date_string
from app.services.categorization import categorizer

class BillExtractor:
    """Extracts merchant, invoice no, dates, amounts, items, and taxes from bill text."""

    @staticmethod
    def extract_currency(text: str) -> str:
        """Identify currency symbol used in document."""
        if "₹" in text or "INR" in text or "Rs" in text or "Rs." in text:
            return "₹"
        if "$" in text or "USD" in text:
            return "$"
        if "€" in text or "EUR" in text:
            return "€"
        if "£" in text or "GBP" in text:
            return "£"
        return "₹"  # default

    @staticmethod
    def extract_merchant(lines: List[str]) -> str:
        """
        Identify vendor or merchant name.
        Typically the top-most bold or prominent non-header line.
        """
        skip_phrases = [
            "tax invoice", "bill of supply", "retail invoice", "cash receipt", "receipt",
            "invoice", "welcome to", "gstin", "gst no", "cin", "pan", "phone", "tel:", "fssai",
            "date", "time", "order no", "bill no", "original for recipient", "duplicate"
        ]

        for line in lines[:8]:
            cleaned = line.strip()
            if not cleaned or len(cleaned) < 3:
                continue
            lower_line = cleaned.lower()
            if any(skip in lower_line for skip in skip_phrases):
                continue
            # Remove leading symbols or punctuation
            cleaned = re.sub(r"^[^\w\s]+", "", cleaned).strip()
            if cleaned and not re.match(r"^[\d\s\-/\:\,\.]+$", cleaned):
                # Cut off long strings
                return cleaned[:60]

        return "Unknown Merchant"

    @staticmethod
    def extract_invoice_number(text: str) -> Optional[str]:
        """Extract invoice or bill identifier."""
        patterns = [
            r"(?:Invoice\s*(?:No|Num|Number|#)|Bill\s*(?:No|#)|Receipt\s*(?:No|#)|Order\s*(?:No|#)|TXN\s*(?:ID|No|#))[\s\:\.\-\#]*([A-Za-z0-9\-_/]+)",
            r"(?:Inv|Bill)\s*[:#]\s*([A-Za-z0-9\-_/]+)"
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                inv = m.group(1).strip()
                if len(inv) >= 3 and not inv.lower().startswith("date"):
                    return inv
        return None

    @staticmethod
    def extract_date_and_time(text: str) -> Tuple[Optional[date], Optional[str]]:
        """Extract transaction date and time."""
        extracted_date = None
        extracted_time = None

        # Date pattern matching
        date_patterns = [
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
            r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b",
            r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b"
        ]
        for pat in date_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                d = parse_date_string(m.group(1))
                if d:
                    extracted_date = d
                    break

        # Time pattern matching
        time_pat = r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\b"
        time_m = re.search(time_pat, text)
        if time_m:
            extracted_time = time_m.group(1).strip()

        return extracted_date, extracted_time

    @staticmethod
    def extract_payment_method(text: str) -> str:
        """Identify payment method from bill text."""
        methods = {
            "UPI": [r"\bupi\b", r"\bgpay\b", r"\bgoogle pay\b", r"\bphonepe\b", r"\bpaytm\b", r"\bbhim\b"],
            "Credit Card": [r"\bcredit card\b", r"\bmastercard\b", r"\bvisa\b", r"\bamex\b"],
            "Debit Card": [r"\bdebit card\b", r"\bpos sale\b", r"\bcard payment\b"],
            "Net Banking": [r"\bnet banking\b", r"\bneft\b", r"\brtgs\b", r"\bimps\b"],
            "Cash": [r"\bcash\b", r"\bcash tendered\b", r"\bcash change\b"]
        }
        text_lower = text.lower()
        for method, patterns in methods.items():
            for pat in patterns:
                if re.search(pat, text_lower):
                    return method

        return "Cash"

    @staticmethod
    def extract_monetary_values(text: str) -> Dict[str, float]:
        """
        Extract subtotal, tax, discount, additional charges and final total.

        Handles common OCR errors where the Indian rupee symbol (₹)
        is incorrectly recognized as a leading digit.
        """
        results = {
            "subtotal": 0.0,
            "tax": 0.0,
            "discount": 0.0,
            "additional_charges": 0.0,
            "total": 0.0
        }

        def extract_numbers(value: str) -> List[float]:
            """Extract numeric values from an OCR line."""
            matches = re.findall(r"\d+(?:[.,]\d{1,2})?", value)
            numbers = []

            for match in matches:
                try:
                    numbers.append(clean_amount(match))
                except Exception:
                    continue

            return numbers

        def normalize_ocr_amount(value: float, reference_total: float = 0.0) -> float:
            """
            OCR sometimes reads ₹ as a leading digit.

            Examples:
                71580.00 -> 1580.00
                2142.20  -> 142.20
                2120     -> 120
                2150     -> 150
            """
            if value <= 0 or reference_total <= 0 or value <= reference_total:
                return value

            value_str = f"{value:.2f}".rstrip("0").rstrip(".")

            # Try removing one or two leading OCR-noise digits.
            for remove_count in (1, 2):
                candidate_str = value_str[remove_count:]

                if not candidate_str:
                    continue

                try:
                    candidate = float(candidate_str)

                    if 0 < candidate <= reference_total:
                        return candidate
                except ValueError:
                    continue

            return value

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # ---------------------------------------------------------
        # 1. FINAL TOTAL
        # ---------------------------------------------------------
        total_patterns = [
            r"(?:Grand\s*Total|Total\s*Amount|Final\s*Total|Net\s*Amount|"
            r"Amount\s*Payable|Balance\s*Due|Total\s*Due|Bill\s*Amount)"
            r".*?([0-9]+(?:[,\.][0-9]{1,2})?)",

            r"^Total\s*[\:\=\-]?\s*([0-9]+(?:[,\.][0-9]{1,2})?)"
        ]

        for pat in total_patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)

            if m:
                results["total"] = clean_amount(m.group(1))

                if results["total"] > 0:
                    break

        # ---------------------------------------------------------
        # 2. SUBTOTAL
        # ---------------------------------------------------------
        for line in lines:
            if re.search(r"\bsub\s*total\b|\bsubtotal\b|\bitem\s*total\b", line, re.I):
                numbers = extract_numbers(line)

                if numbers:
                    # Usually the last number on the subtotal line is the amount.
                    subtotal = numbers[-1]

                    results["subtotal"] = normalize_ocr_amount(
                        subtotal,
                        results["total"]
                    )
                    break

        # ---------------------------------------------------------
        # 3. TAX / GST
        # ---------------------------------------------------------
        tax_sum = 0.0

        for line in lines:
            # "Tax Invoice" is an invoice header, NOT a tax amount.
            if re.search(r"\bTax\s+Invoice\b", line, re.IGNORECASE):
                continue

            if re.search(r"\b(?:CGST|SGST|IGST|GST|VAT|Tax)\b", line, re.IGNORECASE):

                numbers = extract_numbers(line)

                if not numbers:
                    continue

                # On lines such as:
                # CGST @9% On ₹1580.00 : ₹142.20
                #
                # The LAST number is the actual tax amount.
                tax_amount = numbers[-1]

                tax_amount = normalize_ocr_amount(
                    tax_amount,
                    results["total"]
                )

                if tax_amount > 0 and (
                    results["total"] == 0 or tax_amount <= results["total"]
                ):
                    tax_sum += tax_amount

        results["tax"] = round(tax_sum, 2)

        # ---------------------------------------------------------
        # 4. DISCOUNT
        # ---------------------------------------------------------
        for line in lines:
            if re.search(
                r"\b(?:Discount|Disc|Savings|Promo|Coupon)\b",
                line,
                re.I
            ):
                numbers = extract_numbers(line)

                if numbers:
                    results["discount"] = normalize_ocr_amount(
                        numbers[-1],
                        results["total"]
                    )
                    break

        # ---------------------------------------------------------
        # 5. ADDITIONAL CHARGES
        # ---------------------------------------------------------
        for line in lines:
            if re.search(
                r"\b(?:Service\s*Charge|Delivery\s*Fee|Delivery\s*Charge|"
                r"Packaging\s*Charge|Convenience\s*Fee|Tips?)\b",
                line,
                re.I
            ):
                numbers = extract_numbers(line)

                if numbers:
                    results["additional_charges"] = normalize_ocr_amount(
                        numbers[-1],
                        results["total"]
                    )
                    break

        # ---------------------------------------------------------
        # 6. BALANCING / FALLBACK
        # ---------------------------------------------------------
        tot = results["total"]
        sub = results["subtotal"]
        tax = results["tax"]
        disc = results["discount"]
        charges = results["additional_charges"]

        if tot == 0.0 and sub > 0.0:
            results["total"] = round(
                sub + tax + charges - disc,
                2
            )

        elif tot > 0.0 and sub == 0.0:
            results["subtotal"] = round(
                max(0.0, tot - tax - charges + disc),
                2
            )

        return results

    @staticmethod
    def extract_line_items(text: str) -> List[Dict[str, Any]]:
        """
        Extract line items from OCR text.

        Handles common OCR problems:
        - ₹ interpreted as a leading digit
        - ₹ interpreted as %, Z, M, etc.
        - partially corrupted numeric fields
        - missing price/amount for an item
        - OCR corruption of line totals
        """

        # ---------------------------------------------------------
        # IMPORTANT:
        # Use the already-corrected monetary extraction to obtain
        # the real subtotal and total.
        #
        # Example OCR:
        #   Sub Total : 71580.00
        #
        # Correct monetary extraction:
        #   subtotal = 1580.00
        # ---------------------------------------------------------
        monetary = BillExtractor.extract_monetary_values(text)

        subtotal = monetary.get("subtotal", 0.0)
        total_amount = monetary.get("total", 0.0)

        # Use subtotal as the primary reference for line-item
        # amount correction.
        reference_amount = max(subtotal, total_amount)

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        # ---------------------------------------------------------
        # Locate the beginning of the item table.
        # ---------------------------------------------------------
        start_index = 0

        for i, line in enumerate(lines):
            if re.search(r"\bParticulars\b", line, re.IGNORECASE):
                start_index = i + 1
                break

        # ---------------------------------------------------------
        # Stop when the bill summary starts.
        # ---------------------------------------------------------
        stop_pattern = re.compile(
            r"\b(?:"
            r"Sub\s*Total|"
            r"Subtotal|"
            r"CGST|"
            r"SGST|"
            r"IGST|"
            r"GST|"
            r"Food\s*Total|"
            r"Grand\s*Total|"
            r"Total|"
            r"E\.?\s*&?\s*O\.?\s*E\.?|"
            r"Thank\s*You"
            r")\b",
            re.IGNORECASE
        )

        item_lines = []

        for line in lines[start_index:]:

            if stop_pattern.search(line):
                break

            # Ignore column/header lines.
            if re.search(
                r"^\s*(?:Qty|Rate|Amount|Date|Bill\s*No|T\.No|W\.No)",
                line,
                re.IGNORECASE
            ):
                continue

            item_lines.append(line)

        # ---------------------------------------------------------
        # Correct OCR-corrupted monetary values.
        #
        # Examples:
        #   2150 -> 150
        #   2120 -> 120
        #
        # The correction is only applied when the value is larger
        # than the actual bill amount.
        # ---------------------------------------------------------
        def normalize_amount(value: float) -> float:
            if value <= 0:
                return 0.0

            if reference_amount <= 0:
                return value

            # Example:
            # 2120 -> 120
            # 2150 -> 150
            #
            # Keep removing the leading OCR character/digit until
            # the amount becomes reasonable for this receipt.
            candidate = str(int(value))

            while (
                len(candidate) > 1
                and float(candidate) > reference_amount
            ):
                candidate = candidate[1:]

            try:
                return float(candidate)
            except ValueError:
                return value

        # ---------------------------------------------------------
        # Extract numeric values from an OCR line.
        #
        # This intentionally allows OCR text such as:
        #
        #   M0
        #   Z40
        #   %220
        #
        # because the numeric portion can still be recovered.
        # ---------------------------------------------------------
        def extract_numbers(line: str) -> List[float]:
            matches = re.findall(
                r"\d+(?:[.,]\d{1,2})?",
                line
            )

            numbers = []

            for value in matches:
                try:
                    numbers.append(
                        normalize_amount(
                            clean_amount(value)
                        )
                    )
                except Exception:
                    continue

            return numbers

        parsed_items: List[Dict[str, Any]] = []

        # ---------------------------------------------------------
        # Parse every potential item line.
        # ---------------------------------------------------------
        for line in item_lines:

            # Find the first number anywhere in the line.
            #
            # This is important for OCR such as:
            #
            # HANDIPANEER =—Oi2~...
            #
            # where the quantity is attached to corrupted OCR
            # characters rather than separated cleanly.
            qty_match = re.search(r"(\d+)", line)

            if not qty_match:
                continue

            try:
                quantity = float(qty_match.group(1))
            except ValueError:
                continue

            if quantity <= 0:
                continue

            # Everything before the quantity is the item name.
            raw_name = line[:qty_match.start()]

            # Remove OCR punctuation/noise.
            name = re.sub(
                r"[^A-Za-z0-9&./\-\s]",
                " ",
                raw_name
            )

            name = re.sub(r"\s+", " ", name).strip()

            # Remove small OCR fragments that sometimes remain
            # immediately before the quantity.
            name = re.sub(
                r"\s+(?:O|0|Oi|Ol|i)\s*$",
                "",
                name,
                flags=re.IGNORECASE
            ).strip()

            if len(name) < 2:
                continue

            # Ignore obvious non-item text.
            # Ignore invoice/header information that can contain numbers.
            if re.search(
                r"(?:tax\s+invoice|invoice|bill\s*(?:no|number)?|"
                r"date\s*:|t\.?\s*no\.?|w\.?\s*no\.?|"
                r"particulars|qty|rate|amount)",
                name,
                re.IGNORECASE
            ):
                continue

            # Extract everything after the quantity.
            remaining_text = line[qty_match.end():]

            numbers = extract_numbers(remaining_text)

            # If OCR repeated the quantity as a fake numeric value,
            # don't treat that quantity as a price.
            if (
                len(numbers) == 1
                and numbers[0] == quantity
            ):
                numbers = []

            unit_price = 0.0
            total_price = 0.0

            # -----------------------------------------------------
            # Two numeric values:
            #
            #   Qty  UnitPrice  Total
            #
            # Example:
            #   2  2150  300
            #
            # becomes:
            #   2  150  300
            # -----------------------------------------------------
            if len(numbers) >= 2:

                unit_price = numbers[-2]
                total_price = numbers[-1]

            # -----------------------------------------------------
            # One numeric value:
            #
            # Usually this is the total amount.
            # Unit price can then be calculated from quantity.
            # -----------------------------------------------------
            elif len(numbers) == 1:

                total_price = numbers[0]

            # -----------------------------------------------------
            # No usable numeric values.
            #
            # The amount will be recovered later from the subtotal
            # if this is the only missing item.
            # -----------------------------------------------------
            else:
                unit_price = 0.0
                total_price = 0.0

            # -----------------------------------------------------
            # Recover corrupted/missing unit prices.
            #
            # Examples:
            #
            # PLAIN RAITA 2 M0 220
            # -> unit = 110, total = 220
            #
            # JEERA RICE 2 10 220
            # -> OCR unit 10 is inconsistent with 220/2,
            #    so use 110.
            #
            # TANDURI ROTI BUTTER 8 5 120
            # -> Keep ₹5 because the receipt explicitly gives
            #    ₹120 as its line total and the mismatch is not
            #    extreme enough to assume OCR corruption.
            # -----------------------------------------------------
            if quantity > 0 and total_price > 0:

                implied_unit_price = round(
                    total_price / quantity,
                    2
                )

                if unit_price <= 0:
                    unit_price = implied_unit_price

                elif (
                    implied_unit_price >= 50
                    and unit_price > 0
                    and implied_unit_price / unit_price >= 5
                ):
                    # Strong indication that OCR lost leading
                    # digits from the unit price.
                    unit_price = implied_unit_price

            parsed_items.append(
                {
                    "item_name": name,
                    "quantity": quantity,
                    "unit_price": round(unit_price, 2),
                    "total_price": round(total_price, 2)
                }
            )

        # ---------------------------------------------------------
        # Recover a completely missing item amount.
        #
        # Example:
        #
        # Known items:
        #   300 + 220 + 220 + 120 + 120 + 200
        #   = 1180
        #
        # Receipt subtotal:
        #   1580
        #
        # Missing:
        #   1580 - 1180 = 400
        #
        # For HANDIPANEER quantity = 2:
        #   400 / 2 = 200
        # ---------------------------------------------------------
        if subtotal > 0 and parsed_items:

            known_total = round(
                sum(
                    item["total_price"]
                    for item in parsed_items
                    if item["total_price"] > 0
                ),
                2
            )

            missing_items = [
                item
                for item in parsed_items
                if item["total_price"] <= 0
            ]

            if len(missing_items) == 1:

                missing_item = missing_items[0]

                remaining_amount = round(
                    subtotal - known_total,
                    2
                )

                if remaining_amount > 0:

                    missing_item["total_price"] = remaining_amount

                    if missing_item["quantity"] > 0:
                        missing_item["unit_price"] = round(
                            remaining_amount /
                            missing_item["quantity"],
                            2
                        )

        return parsed_items

    @classmethod
    def extract(cls, raw_text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete parsing pipeline from raw text to structured expense dictionary.
        """
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        
        merchant = cls.extract_merchant(lines)
        invoice_no = cls.extract_invoice_number(raw_text)
        exp_date, exp_time = cls.extract_date_and_time(raw_text)
        payment_method = cls.extract_payment_method(raw_text)
        currency = cls.extract_currency(raw_text)
        monetary = cls.extract_monetary_values(raw_text)
        items = cls.extract_line_items(raw_text)

        # Categorize based on merchant and items
        item_names = [it["item_name"] for it in items]
        category, confidence = categorizer.categorize(merchant, item_names, raw_text)

        warnings = []
        if monetary["total"] == 0.0:
            warnings.append("Could not automatically identify total amount from receipt text.")
        if exp_date is None:
            warnings.append("Date was not detected; defaulted to today's date.")
            exp_date = date.today()
        if merchant == "Unknown Merchant":
            warnings.append("Merchant name could not be reliably determined.")

        return {
            "merchant": merchant,
            "invoice_number": invoice_no,
            "date": exp_date,
            "time": exp_time,
            "currency": currency,
            "subtotal": monetary["subtotal"],
            "tax": monetary["tax"],
            "discount": monetary["discount"],
            "additional_charges": monetary["additional_charges"],
            "total": monetary["total"],
            "payment_method": payment_method,
            "category": category,
            "category_confidence": round(confidence, 2),
            "items": items,
            "raw_text": raw_text,
            "source_file": filename,
            "warnings": warnings
        }
