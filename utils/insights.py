"""Extra analysis signals for the dashboard.

Provides:
  * experience match (0-5 rating) from years/seniority signals
  * skill priority (High / Medium / Low) for missing skills
  * partial matches - skills mentioned only weakly in the resume
  * overall strength verdict
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .skills import extract_skills

# --------------------------------------------------------------------------- #
# Experience match
# --------------------------------------------------------------------------- #

_YEAR_PATTERNS = [
    r"(\d+)\s*\+?\s*years?",
    r"(\d+)\s*\+?\s*yrs?",
]

_SENIORITY = {
    "intern": 0, "fresh": 0, "graduate": 0, "entry": 1, "junior": 1,
    "associate": 2, "mid": 3, "senior": 5, "lead": 6, "principal": 7,
    "manager": 6, "head": 8,
}


def _years_required(text: str) -> int:
    """Best guess at the years of experience a job asks for."""
    lowered = text.lower()
    years = []
    for pattern in _YEAR_PATTERNS:
        years += [int(m) for m in re.findall(pattern, lowered) if m.isdigit()]
    if years:
        return min(max(years), 15)

    for word, level in _SENIORITY.items():
        if word in lowered:
            return level
    return 2


def _years_held(text: str) -> int:
    """Best guess at the candidate's years of experience."""
    lowered = text.lower()
    years = []
    for pattern in _YEAR_PATTERNS:
        years += [int(m) for m in re.findall(pattern, lowered) if m.isdigit()]

    # Also infer from date ranges like "2021 - 2024" or "2022-present".
    ranges = re.findall(r"(20\d{2})\s*[-–to]+\s*(20\d{2}|present|current)", lowered)
    for start, end in ranges:
        end_year = 2026 if end in ("present", "current") else int(end)
        span = end_year - int(start)
        if 0 < span < 25:
            years.append(span)

    return min(max(years), 15) if years else 1


def experience_match(resume_text: str, job_text: str) -> Dict[str, object]:
    """Return a 0-5 experience match rating with context."""
    required = _years_required(job_text)
    held = _years_held(resume_text)

    if required <= 0:
        ratio = 1.0
    else:
        ratio = held / required

    rating = round(min(ratio, 1.0) * 5, 1)
    # Give partial credit rather than a harsh zero for near misses.
    if held > 0 and rating < 1.0:
        rating = max(rating, 1.0)

    if rating >= 4.0:
        label = "Good Match"
    elif rating >= 2.5:
        label = "Fair Match"
    else:
        label = "Below Requirement"

    return {
        "rating": rating,
        "label": label,
        "required": required,
        "held": held,
    }


# --------------------------------------------------------------------------- #
# Skill priority
# --------------------------------------------------------------------------- #

_HIGH_SIGNALS = ["required", "must have", "essential", "strong", "proficient"]
_LOW_SIGNALS = ["nice to have", "plus", "bonus", "preferred", "desirable"]


def skill_priority(skill: str, job_text: str) -> str:
    """Classify how important a skill is to the job: High / Medium / Low."""
    lowered = job_text.lower()
    if skill not in lowered:
        return "Medium"

    # Look at the sentence containing the skill.
    sentences = re.split(r"[.\n]", lowered)
    context = " ".join(s for s in sentences if skill in s)

    if any(sig in context for sig in _LOW_SIGNALS):
        return "Low"
    if any(sig in context for sig in _HIGH_SIGNALS):
        return "High"

    # Frequency is a decent proxy for importance.
    return "High" if lowered.count(skill) >= 2 else "Medium"


def prioritise_missing(missing: List[str], job_text: str) -> List[Tuple[str, str]]:
    """Return missing skills sorted by priority (High first)."""
    order = {"High": 0, "Medium": 1, "Low": 2}
    scored = [(s, skill_priority(s, job_text)) for s in missing]
    return sorted(scored, key=lambda x: (order[x[1]], x[0]))


# --------------------------------------------------------------------------- #
# Partial matches
# --------------------------------------------------------------------------- #


def partial_matches(resume_text: str, job_text: str) -> List[str]:
    """Skills the job wants that the resume only mentions in passing.

    A skill counts as 'partial' when it appears exactly once in the resume
    (a bare keyword) rather than being backed by repeated use.
    """
    job_skills = set(extract_skills(job_text))
    resume_lower = resume_text.lower()

    partial = []
    for skill in job_skills:
        count = resume_lower.count(skill)
        if count == 1:
            partial.append(skill)
    return sorted(partial)


# --------------------------------------------------------------------------- #
# Overall verdict
# --------------------------------------------------------------------------- #


def overall_strength(score: float, ats: float, exp_rating: float) -> Dict[str, str]:
    """Blend the signals into a single verdict."""
    blended = (score * 0.4) + (ats * 0.4) + (exp_rating / 5 * 100 * 0.2)

    if blended >= 75:
        return {
            "label": "Excellent",
            "detail": "Your resume is strong and well optimized for this role.",
        }
    if blended >= 55:
        return {
            "label": "Good",
            "detail": "Solid foundation. A few targeted edits will lift it further.",
        }
    if blended >= 35:
        return {
            "label": "Fair",
            "detail": "Worth tailoring more closely to this job's keywords.",
        }
    return {
        "label": "Needs Work",
        "detail": "Rework the resume around this job's core requirements.",
    }
