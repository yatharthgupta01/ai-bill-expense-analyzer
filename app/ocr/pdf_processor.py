"""
PDF document processing and direct/OCR text extraction.
"""
import io
from pathlib import Path
from typing import Tuple, Optional
from pypdf import PdfReader
from PIL import Image

from app.ocr.image_processor import extract_text_from_image

def extract_text_from_pdf(pdf_input) -> Tuple[str, bool, bool, Optional[str]]:
    """
    Extract text from a PDF file (Path, bytes, or file stream).
    Attempts direct text extraction first. If the PDF contains no text (scanned),
    attempts to extract embedded images and perform OCR.

    Returns:
        (extracted_text, is_scanned, success, error_message)
    """
    try:
        if isinstance(pdf_input, (str, Path)):
            reader = PdfReader(str(pdf_input))
        elif hasattr(pdf_input, "read"):
            reader = PdfReader(pdf_input)
        elif isinstance(pdf_input, bytes):
            reader = PdfReader(io.BytesIO(pdf_input))
        else:
            return "", False, False, "Invalid PDF input source."

        if len(reader.pages) == 0:
            return "", False, False, "The uploaded PDF has no pages."

        # 1. Attempt direct text extraction
        extracted_pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_pages.append(page_text.strip())

        full_text = "\n\n".join(extracted_pages).strip()

        # If we got meaningful text (more than 20 characters), return it as digital PDF
        if len(full_text) >= 20:
            return full_text, False, True, None

        # 2. Scanned PDF: Extract images from pages and OCR them
        scanned_texts = []
        found_any_image = False

        for page in reader.pages:
            for img_obj in page.images:
                found_any_image = True
                try:
                    img_bytes = img_obj.data
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    img_text, ok, err = extract_text_from_image(pil_img)
                    if ok and img_text:
                        scanned_texts.append(img_text)
                except Exception:
                    continue

        if scanned_texts:
            return "\n\n".join(scanned_texts).strip(), True, True, None

        if not found_any_image:
            return (
                "",
                True,
                False,
                "No selectable text or extractable images found in the PDF. Please ensure the document is not password-protected or empty."
            )

        return (
            "",
            True,
            False,
            "Could not extract readable text from scanned PDF images. Please enter expense details manually in the review screen."
        )

    except Exception as e:
        return "", False, False, f"Failed to process PDF: {str(e)}"
