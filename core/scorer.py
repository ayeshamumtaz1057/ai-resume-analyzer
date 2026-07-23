"""Turn a parsed resume + job description into scores.

Overall match = 55% skill coverage + 30% TF-IDF text similarity + 15% resume quality.
Weights live in `WEIGHTS` so they are easy to tune and easy to explain in a README.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .extractor import extract_skills, skill_frequency
from .parser import ParsedResume
from .skills_db import CORE_TECHNICAL, IMPLIES

WEIGHTS = {"skills": 0.55, "similarity": 0.30, "quality": 0.15}

# Naming a skill once already earns most of the credit; repeated use across
# sections is what separates a keyword from demonstrated depth.
BASE_CREDIT = 70
DEPTH_BONUS = 15
DEPTH_FULL = 3

# Cosine similarity between a long resume and a short posting is structurally
# low (0.15-0.35 is typical for a good match), so we rescale before weighting.
SIMILARITY_GAIN = 2.2

_METRIC = re.compile(r"(\d+(\.\d+)?\s*%|\$\s?\d|\b\d{2,}\b|\bx\d+\b)")
_ACTION_VERBS = {
    "built", "designed", "led", "implemented", "developed", "automated", "reduced",
    "increased", "improved", "launched", "deployed", "optimised", "optimized",
    "analysed", "analyzed", "created", "shipped", "owned", "scaled", "migrated",
}


@dataclass
class SkillResult:
    name: str
    in_resume: bool
    coverage: int  # 0-100, how strongly the resume evidences it
    evidence: str = "direct"  # "direct", "implied", or "none"


@dataclass
class Analysis:
    overall: int
    similarity: int
    skill_coverage: int
    quality: int
    matched: list[SkillResult]
    missing: list[SkillResult]
    section_scores: dict[str, int]
    jd_skills: list[str]
    resume_skills: list[str]

    @property
    def verdict(self) -> str:
        if self.overall >= 80:
            return "Great match"
        if self.overall >= 65:
            return "Solid match"
        if self.overall >= 50:
            return "Partial match"
        return "Weak match"


def _text_similarity(resume: str, jd: str) -> float:
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        matrix = vec.fit_transform([resume, jd])
    except ValueError:
        return 0.0
    return float(cosine_similarity(matrix[0], matrix[1])[0][0])


def _coverage_for(skill: str, freq: dict[str, int], present: set[str]) -> tuple[int, str]:
    """Score how well the resume evidences one skill.

    Direct mentions scale with repetition. If the skill is never named, we look
    for tools that imply it — listing PyTorch is real evidence of deep learning.
    """
    hits = freq.get(skill, 0)
    if hits:
        depth = min(hits, DEPTH_FULL) - 1
        return min(100, BASE_CREDIT + DEPTH_BONUS * depth), "direct"

    best = 0.0
    for tool in present:
        best = max(best, IMPLIES.get(tool, {}).get(skill, 0.0))
    if best:
        return int(round(best * 100)), "implied"
    return 0, "none"


def _quality_score(resume: ParsedResume) -> tuple[int, dict[str, int]]:
    """Heuristics an actual recruiter would notice, scored per section."""
    text = resume.raw_text
    lowered = text.lower()
    sections = resume.sections

    def has(name: str) -> bool:
        return bool(sections.get(name, "").strip())

    metrics = len(_METRIC.findall(text))
    verbs = sum(1 for v in _ACTION_VERBS if v in lowered)

    scores = {
        "Summary": 90 if has("summary") else 40,
        "Experience": min(100, 45 + metrics * 4 + verbs * 3) if has("experience") else 30,
        "Skills": min(100, 50 + len(extract_skills(sections.get("skills", ""))) * 6)
        if has("skills")
        else 35,
        "Projects": min(100, 55 + resume.bullet_count * 2) if has("projects") else 30,
        "Education": 95 if has("education") else 45,
    }

    # Length penalty: under 300 words is thin, over 1200 is a wall of text.
    words = resume.word_count
    if words < 300:
        scores["Summary"] = max(20, scores["Summary"] - 25)
    elif words > 1200:
        scores["Experience"] = max(20, scores["Experience"] - 15)

    overall = int(round(sum(scores.values()) / len(scores)))
    return overall, scores


def analyse(resume: ParsedResume, job_description: str) -> Analysis:
    jd_skills = extract_skills(job_description)
    resume_skills = extract_skills(resume.raw_text)
    freq = skill_frequency(resume.raw_text)

    results = []
    for skill in sorted(jd_skills):
        cov, evidence = _coverage_for(skill, freq, resume_skills)
        results.append(SkillResult(skill, cov > 0, cov, evidence))

    # Weight the skills the job actually hinges on.
    if results:
        total_w = sum(2.0 if r.name in CORE_TECHNICAL else 1.0 for r in results)
        earned = sum((2.0 if r.name in CORE_TECHNICAL else 1.0) * r.coverage / 100 for r in results)
        skill_pct = 100 * earned / total_w
    else:
        # No recognisable skills in the JD — lean entirely on text similarity.
        skill_pct = 0.0

    sim = _text_similarity(resume.raw_text, job_description) * 100
    quality, section_scores = _quality_score(resume)

    if jd_skills:
        overall = (
            WEIGHTS["skills"] * skill_pct
            + WEIGHTS["similarity"] * min(100, sim * SIMILARITY_GAIN)  # cosine on short JDs runs low
            + WEIGHTS["quality"] * quality
        )
    else:
        overall = 0.6 * min(100, sim * SIMILARITY_GAIN) + 0.4 * quality

    return Analysis(
        overall=int(round(overall)),
        similarity=int(round(sim)),
        skill_coverage=int(round(skill_pct)),
        quality=quality,
        matched=[r for r in results if r.in_resume],
        missing=[r for r in results if not r.in_resume],
        section_scores=section_scores,
        jd_skills=sorted(jd_skills),
        resume_skills=sorted(resume_skills),
    )
