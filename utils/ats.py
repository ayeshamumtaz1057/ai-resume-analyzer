"""ATS (Applicant Tracking System) friendliness scoring.

Estimates how well a resume would survive automated screening. This is a
heuristic score built from signals real ATS parsers care about: standard
section headings, contact details, measurable achievements, keyword coverage
against the job description, and sensible length.
"""

from __future__ import annotations

import re
from typing import Dict, List

from .skills import extract_skills

# Standard headings an ATS looks for when segmenting a resume.
_SECTIONS = {
    "experience": ["experience", "employment", "work history"],
    "education": ["education", "academic"],
    "skills": ["skills", "technical skills", "competencies"],
    "projects": ["projects", "portfolio"],
    "summary": ["summary", "objective", "profile", "about"],
}

_ACTION_VERBS = [
    "built", "developed", "designed", "implemented", "created", "led",
    "managed", "improved", "reduced", "increased", "automated", "analysed",
    "analyzed", "delivered", "launched", "optimised", "optimized",
]


def _has_email(text: str) -> bool:
    return bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text))


def _has_phone(text: str) -> bool:
    return bool(re.search(r"(\+?\d[\d\s\-()]{7,}\d)", text))


def _has_link(text: str) -> bool:
    return bool(re.search(r"(linkedin\.com|github\.com|https?://)", text, re.I))


def _sections_found(text: str) -> List[str]:
    lowered = text.lower()
    found = []
    for name, variants in _SECTIONS.items():
        if any(v in lowered for v in variants):
            found.append(name)
    return found


def _quantified_count(text: str) -> int:
    """Count bullets that contain numbers/percentages (measurable impact)."""
    return len(re.findall(r"\b\d+(\.\d+)?\s*(%|percent|k\b|\+)?", text))


def compute_ats_score(resume_text: str, job_text: str = "") -> Dict[str, object]:
    """Return an ATS score (0-100) plus a breakdown of the checks.

    Returns:
        dict with keys ``score`` (float), ``checks`` (list of dicts with
        ``label``, ``passed``, ``detail``).
    """
    if not resume_text.strip():
        return {"score": 0.0, "checks": []}

    checks: List[Dict[str, object]] = []
    points = 0.0

    # 1. Contact information (15)
    contact_bits = sum([_has_email(resume_text), _has_phone(resume_text), _has_link(resume_text)])
    contact_pts = (contact_bits / 3) * 15
    points += contact_pts
    checks.append({
        "label": "Contact details",
        "passed": contact_bits >= 2,
        "detail": f"{contact_bits}/3 found (email, phone, link)",
    })

    # 2. Standard sections (25)
    sections = _sections_found(resume_text)
    section_pts = min(len(sections) / 4, 1.0) * 25
    points += section_pts
    checks.append({
        "label": "Standard sections",
        "passed": len(sections) >= 3,
        "detail": ", ".join(sections) or "none detected",
    })

    # 3. Keyword coverage vs. job description (30)
    if job_text.strip():
        job_skills = set(extract_skills(job_text))
        resume_skills = set(extract_skills(resume_text))
        coverage = len(job_skills & resume_skills) / len(job_skills) if job_skills else 0.0
        keyword_pts = coverage * 30
        detail = f"{len(job_skills & resume_skills)}/{len(job_skills)} job keywords present"
    else:
        coverage = 0.0
        keyword_pts = 15.0  # neutral credit when no job text given
        detail = "no job description provided"
    points += keyword_pts
    checks.append({
        "label": "Keyword match",
        "passed": coverage >= 0.5,
        "detail": detail,
    })

    # 4. Quantified achievements (15)
    numbers = _quantified_count(resume_text)
    quant_pts = min(numbers / 6, 1.0) * 15
    points += quant_pts
    checks.append({
        "label": "Measurable results",
        "passed": numbers >= 3,
        "detail": f"{numbers} numeric mentions",
    })

    # 5. Action verbs (8)
    lowered = resume_text.lower()
    verbs = sum(1 for v in _ACTION_VERBS if v in lowered)
    verb_pts = min(verbs / 5, 1.0) * 8
    points += verb_pts
    checks.append({
        "label": "Action verbs",
        "passed": verbs >= 3,
        "detail": f"{verbs} strong verbs used",
    })

    # 6. Reasonable length (7)
    words = len(resume_text.split())
    good_length = 250 <= words <= 1200
    points += 7 if good_length else 3
    checks.append({
        "label": "Length",
        "passed": good_length,
        "detail": f"{words} words",
    })

    return {"score": round(min(points, 100.0), 1), "checks": checks}
