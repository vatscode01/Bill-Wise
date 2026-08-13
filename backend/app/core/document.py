import base64
from typing import Optional
import pdfplumber

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file using pdfplumber.
    """
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def encode_image_to_base64(file_path: str) -> str:
    """
    Reads an image file and returns its base64 encoded string.
    """
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
