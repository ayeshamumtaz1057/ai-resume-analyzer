"""Read a resume PDF and split it into recognisable sections."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from io import BytesIO

from pypdf import PdfReader

# Heading -> the section bucket we file it under.
SECTION_PATTERNS: dict[str, list[str]] = {
    "summary": ["summary", "profile", "objective", "about me", "professional summary"],
    "experience": ["experience", "employment", "work history", "professional experience", "internship"],
    "skills": ["skills", "technical skills", "core competencies", "technologies", "tech stack"],
    "projects": ["projects", "personal projects", "academic projects", "portfolio"],
    "education": ["education", "academic background", "qualifications"],
    "certifications": ["certifications", "certificates", "licenses", "courses"],
}

_BULLET = re.compile(r"^\s*[\u2022\u25cf\u25aa\-\*\u2013]\s+", re.MULTILINE)
_WHITESPACE = re.compile(r"[ \t]{2,}")


@dataclass
class ParsedResume:
    raw_text: str
    sections: dict[str, str] = field(default_factory=dict)
    page_count: int = 0

    @property
    def word_count(self) -> int:
        return len(self.raw_text.split())

    @property
    def bullet_count(self) -> int:
        return len(_BULLET.findall(self.raw_text))


class ResumeParseError(RuntimeError):
    """Raised when the PDF yields no usable text."""


def extract_text(file_bytes: bytes) -> tuple[str, int]:
    """Pull text out of a PDF. Returns (text, page_count)."""
    reader = PdfReader(BytesIO(file_bytes))
    pages = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(pages)
    text = _WHITESPACE.sub(" ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text.split()) < 30:
        raise ResumeParseError(
            "This PDF has almost no selectable text. It is probably a scan or an "
            "image export. Re-export it from Word or Google Docs and upload again."
        )
    return text, len(pages)


def _match_heading(line: str) -> str | None:
    """Return the section key if this line looks like a section heading."""
    cleaned = re.sub(r"[^a-z ]", "", line.lower()).strip()
    if not cleaned or len(cleaned.split()) > 4:
        return None
    # Headings are short and usually stand alone on their own line.
    for key, variants in SECTION_PATTERNS.items():
        if any(cleaned == v or cleaned.startswith(v) for v in variants):
            return key
    return None


def split_sections(text: str) -> dict[str, str]:
    """Bucket resume lines under the last heading we saw."""
    sections: dict[str, list[str]] = {}
    current = "header"
    for line in text.splitlines():
        key = _match_heading(line.strip())
        if key:
            current = key
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


def parse_resume(file_bytes: bytes) -> ParsedResume:
    text, pages = extract_text(file_bytes)
    return ParsedResume(raw_text=text, sections=split_sections(text), page_count=pages)
