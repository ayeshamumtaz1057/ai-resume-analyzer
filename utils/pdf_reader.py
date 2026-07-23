"""PDF reading utilities (PyPDF2).

Extracts plain text from a PDF resume. Accepts a path, raw bytes,
BytesIO, or a Streamlit UploadedFile.
"""

from __future__ import annotations

import io
from typing import Union

from PyPDF2 import PdfReader

PDFSource = Union[str, bytes, io.BytesIO]


def _to_stream(source: PDFSource) -> io.BytesIO:
    """Normalise any accepted input into a BytesIO stream."""
    if isinstance(source, str):
        with open(source, "rb") as fh:
            return io.BytesIO(fh.read())
    if isinstance(source, bytes):
        return io.BytesIO(source)
    if isinstance(source, io.BytesIO):
        source.seek(0)
        return source
    # File-like object (e.g. Streamlit's UploadedFile).
    return io.BytesIO(source.read())


def extract_text_from_pdf(source: PDFSource) -> str:
    """Return all extractable text from a PDF, page by page."""
    stream = _to_stream(source)
    reader = PdfReader(stream)

    pages_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(text)

    return "\n".join(pages_text).strip()


if __name__ == "__main__":  # pragma: no cover
    import sys
    if len(sys.argv) > 1:
        print(extract_text_from_pdf(sys.argv[1])[:1000])
    else:
        print("Usage: python pdf_reader.py <path-to-pdf>")
