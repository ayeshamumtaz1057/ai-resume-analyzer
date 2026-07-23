"""Similarity scoring between a resume and a job description.

Uses TF-IDF vectorisation + cosine similarity. This is lightweight (no large
model downloads), deterministic, and works well on free hosting tiers.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocess import clean_text


def compute_similarity(resume_text: str, job_text: str) -> float:
    """Return a 0–100 match score between a resume and a job description.

    Args:
        resume_text: Raw resume text.
        job_text: Raw job description text.

    Returns:
        A percentage (0.0–100.0) rounded to two decimals. Returns 0.0 if
        either input is empty.
    """
    resume_clean = clean_text(resume_text)
    job_clean = clean_text(job_text)

    if not resume_clean or not job_clean:
        return 0.0

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([resume_clean, job_clean])
    score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]

    return round(float(score) * 100, 2)
