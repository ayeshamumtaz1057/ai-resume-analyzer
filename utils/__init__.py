"""Utility package for the AI Resume Analyzer.

Exposes the core helpers so callers can do e.g. ``from utils import extract_text_from_pdf``.
"""

from .pdf_reader import extract_text_from_pdf
from .preprocess import clean_text, tokenize
from .similarity import compute_similarity
from .skills import extract_skills, compare_skills, SKILLS_DB
from .ai_helper import generate_suggestions
from .ats import compute_ats_score
from .extras import (
    rewrite_bullets,
    generate_cover_letter,
    generate_interview_qa,
    estimate_salary,
    format_salary,
    build_roadmap,
)

__all__ = [
    "extract_text_from_pdf",
    "clean_text",
    "tokenize",
    "compute_similarity",
    "extract_skills",
    "compare_skills",
    "SKILLS_DB",
    "generate_suggestions",
    "compute_ats_score",
    "rewrite_bullets",
    "generate_cover_letter",
    "generate_interview_qa",
    "estimate_salary",
    "format_salary",
    "build_roadmap",
]
