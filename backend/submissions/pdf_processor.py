from __future__ import annotations
from PyPDF2 import PdfReader
from io import StringIO
from pdfminer.high_level import extract_text_to_fp

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    reader = PdfReader(pdf_path)
    parts = []
    for pg in reader.pages:
        t = pg.extract_text() or ""
        if t:
            parts.append(t.strip())
    text = "\n\n".join(parts)
    
    if text.strip():
        return text
    out = StringIO()
    with open(pdf_path, "rb") as f:
        extract_text_to_fp(f, out, laparams=None)
    return out.getvalue().strip()
