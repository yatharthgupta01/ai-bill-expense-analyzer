"""
Service layer coordinating document extraction, validation, and expense persistence.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import date

from app.ocr.image_processor import extract_text_from_image
from app.ocr.pdf_processor import extract_text_from_pdf
from app.ocr.extractor import BillExtractor
from app.database.repository import ExpenseRepository
from app.database.models import Expense
from app.utils.validation import validate_expense_data

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class ExpenseService:
    """Coordinates bill processing, extraction, validation, and database operations."""

    @staticmethod
    def process_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Process an uploaded document (Image or PDF), extract text via OCR/direct extraction,
        and parse into structured expense draft for user review.
        """
        ext = filename.lower().split(".")[-1]
        raw_text = ""
        is_scanned = False
        error_msg = None

        # 1. Route based on file extension
        if ext == "pdf":
            raw_text, is_scanned, success, err = extract_text_from_pdf(file_bytes)
            if not success:
                error_msg = err or "Could not extract readable text from PDF."
        elif ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
            raw_text, success, err = extract_text_from_image(file_bytes)
            print("\n========== OCR TEXT ==========")
            print(raw_text)
            print("========== END OCR TEXT ==========\n")
            if not success:
                return {
                    "success": False,
                    "error": err or "Image OCR could not be completed.",
                    "draft": None
                }
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: .{ext}. Supported formats: JPG, JPEG, PNG, PDF.",
                "draft": None
            }

        # 2. Extract structured fields from text
        draft = BillExtractor.extract(raw_text or "", filename=filename)
        
        # Save a copy to uploads directory for reference
        try:
            safe_filename = f"{date.today().isoformat()}_{Path(filename).name}"
            dest_path = UPLOAD_DIR / safe_filename
            with open(dest_path, "wb") as f:
                f.write(file_bytes)
            draft["source_file"] = dest_path.name
        except Exception:
            draft["source_file"] = filename

        return {
            "success": True,
            "raw_text": raw_text,
            "is_scanned": is_scanned,
            "error": error_msg,
            "draft": draft
        }

    @staticmethod
    def save_reviewed_expense(draft: Dict[str, Any]) -> Tuple[bool, Optional[Expense], List[str], List[str]]:
        """
        Validate reviewed expense data and persist to the database.
        Returns: (success, saved_expense, warnings, errors)
        """
        is_valid, warnings, errors = validate_expense_data(draft)
        if not is_valid:
            return False, None, warnings, errors

        items = draft.get("items", [])
        saved = ExpenseRepository.create_expense(draft, items=items)
        return True, saved, warnings, errors

    @staticmethod
    def update_expense(expense_id: int, data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, Optional[Expense], List[str], List[str]]:
        """Validate and update an existing expense."""
        is_valid, warnings, errors = validate_expense_data(data)
        if not is_valid:
            return False, None, warnings, errors

        updated = ExpenseRepository.update_expense(expense_id, data, items=items)
        return True, updated, warnings, errors

    @staticmethod
    def delete_expense(expense_id: int) -> bool:
        """Delete an expense record."""
        return ExpenseRepository.delete_expense(expense_id)
