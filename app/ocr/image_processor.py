"""
Image preprocessing and OCR text extraction pipeline.
"""
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

def get_tesseract_cmd() -> Optional[str]:
    """Detect Tesseract OCR executable path from env or standard Windows/Linux locations."""
    env_cmd = os.getenv("TESSERACT_CMD")
    if env_cmd and os.path.isfile(env_cmd):
        return env_cmd

    # Check PATH
    which_cmd = shutil.which("tesseract")
    if which_cmd:
        return which_cmd

    # Standard Windows install locations
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    return None

def is_tesseract_available() -> bool:
    """Check if Tesseract binary is accessible."""
    return get_tesseract_cmd() is not None

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image for optimal OCR extraction:
    1. Convert to Grayscale
    2. Upscale small images
    3. Enhance contrast
    4. Apply slight sharpening
    """
    # Convert RGBA/Palette to RGB then Grayscale
    if image.mode != "L":
        image = image.convert("RGB").convert("L")

    # Resize if too small (OCR works best when text height is 30-50 pixels)
    width, height = image.size
    if width < 1200 or height < 1200:
        scale = max(1200 / width, 1200 / height)
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.8)

    # Sharpen slightly
    image = image.filter(ImageFilter.SHARPEN)

    return image

def extract_text_from_image(image_input) -> Tuple[str, bool, Optional[str]]:
    """
    Extract text from an image (file path, bytes, or PIL Image).
    Returns: (extracted_text, success, error_message)
    """
    try:
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input)
        elif isinstance(image_input, bytes):
            img = Image.open(BytesIO(image_input))
        elif hasattr(image_input, "read"):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            return "", False, "Unsupported image input format."

        processed_img = preprocess_image(img)

        # Configure tesseract executable if found
        cmd = get_tesseract_cmd()
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd

        try:
            # Run OCR with layout analysis
            text = pytesseract.image_to_string(processed_img, config="--psm 6")
            if not text.strip():
                # Retry with default PSM
                text = pytesseract.image_to_string(processed_img, config="--psm 3")
            return text.strip(), True, None
        except pytesseract.TesseractNotFoundError:
            return (
                "",
                False,
                "Tesseract-OCR executable not found on host. Direct PDF extraction and manual editing are fully active. "
                "To enable local image OCR, install Tesseract-OCR and set TESSERACT_CMD in .env."
            )
        except Exception as e:
            return "", False, f"OCR processing error: {str(e)}"

    except Exception as e:
        return "", False, f"Failed to open or process image: {str(e)}"
