"""Skill extraction and gap analysis.

A curated skills dictionary is matched against text using word-boundary
regex so that "r" doesn't match "react" and "go" doesn't match "google".
"""

from __future__ import annotations

import re
from typing import Dict, List

# Curated, extensible skills catalogue grouped by category.
# Add or edit entries here to tune what the analyzer recognises.
SKILLS_DB: Dict[str, List[str]] = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "go", "rust", "ruby", "php", "swift", "kotlin", "scala", "r",
        "matlab", "perl", "dart", "bash", "sql",
    ],
    "Web & Frontend": [
        "html", "css", "react", "angular", "vue", "next.js", "svelte",
        "tailwind", "bootstrap", "jquery", "redux", "webpack", "vite",
    ],
    "Backend & Frameworks": [
        "node.js", "express", "django", "flask", "fastapi", "spring",
        "laravel", "rails", "asp.net", "graphql", "rest api", "grpc",
    ],
    "Data & AI/ML": [
        "machine learning", "deep learning", "nlp", "computer vision",
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
        "keras", "opencv", "matplotlib", "seaborn", "data analysis",
        "data visualization", "statistics", "llm", "hugging face",
    ],
    "Databases": [
        "mysql", "postgresql", "mongodb", "sqlite", "redis", "oracle",
        "cassandra", "dynamodb", "elasticsearch", "firebase",
    ],
    "DevOps & Cloud": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "jenkins", "ci/cd", "git", "github", "gitlab", "linux", "nginx",
        "ansible", "prometheus", "grafana",
    ],
    "Tools & Practices": [
        "agile", "scrum", "jira", "figma", "postman", "unit testing",
        "tdd", "microservices", "oop", "data structures", "algorithms",
    ],
    "Soft Skills": [
        "communication", "leadership", "teamwork", "problem solving",
        "collaboration", "time management", "adaptability", "creativity",
    ],
}

# Flatten to a single lookup list, preserving the category for each skill.
_SKILL_TO_CATEGORY: Dict[str, str] = {
    skill: category
    for category, skills in SKILLS_DB.items()
    for skill in skills
}


def _skill_pattern(skill: str) -> re.Pattern:
    """Build a case-insensitive, boundary-aware regex for a skill.

    Handles special characters like ``+``, ``#`` and ``.`` (c++, c#, node.js)
    which would otherwise break naive word-boundary matching.
    """
    escaped = re.escape(skill)
    # Use lookarounds so tokens like c++ / node.js match without being
    # swallowed by adjacent alphanumerics.
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)


# Pre-compile patterns once at import time for speed.
_COMPILED = {skill: _skill_pattern(skill) for skill in _SKILL_TO_CATEGORY}


def extract_skills(text: str) -> List[str]:
    """Return the sorted, de-duplicated skills found in ``text``."""
    if not text:
        return []

    lowered = text.lower()
    found = {skill for skill, pattern in _COMPILED.items() if pattern.search(lowered)}
    return sorted(found)


def category_of(skill: str) -> str:
    """Return the category label for a known skill (or 'Other')."""
    return _SKILL_TO_CATEGORY.get(skill, "Other")


def compare_skills(resume_text: str, job_text: str) -> Dict[str, List[str]]:
    """Compare resume vs. job skills.

    Returns:
        A dict with three keys:
          - ``matched``:  skills required by the job AND present in the resume
          - ``missing``:  skills required by the job but ABSENT from the resume
          - ``extra``:    skills in the resume not requested by the job
    """
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_text))

    return {
        "matched": sorted(job_skills & resume_skills),
        "missing": sorted(job_skills - resume_skills),
        "extra": sorted(resume_skills - job_skills),
    }
