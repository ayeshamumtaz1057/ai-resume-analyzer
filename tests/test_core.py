"""Run with: pytest -q"""

import pytest

from core.extractor import extract_skills
from core.parser import ParsedResume, split_sections
from core.scorer import analyse

RESUME = """
Summary
Machine learning engineer with 4 years of experience.

Experience
ML Engineer, Acme
- Trained PyTorch models, cut inference latency 35%
- Built Python and SQL pipelines on AWS processing 5000000 events daily

Skills
Python, SQL, PyTorch, scikit-learn, AWS, Docker

Projects
- NLP sentiment classifier using spaCy

Education
MSc Data Science
"""

JD = """Seeking a Machine Learning Engineer skilled in Python, SQL, Deep Learning,
and AWS. Experience with Docker and NLP is a strong plus."""


def make(text=RESUME):
    return ParsedResume(raw_text=text, sections=split_sections(text), page_count=1)


def test_sections_are_detected():
    sections = split_sections(RESUME)
    for key in ("summary", "experience", "skills", "projects", "education"):
        assert key in sections


def test_extractor_finds_canonical_names():
    found = extract_skills("Experienced in sklearn, pytorch and postgres.")
    assert {"scikit-learn", "PyTorch", "SQL"} <= found


def test_extractor_ignores_substrings():
    # "R" must not match inside "React"; "go" must not match inside "google".
    found = extract_skills("I use React at Google.")
    assert "R" not in found
    assert "Go" not in found


def test_strong_resume_scores_well():
    result = analyse(make(), JD)
    assert result.overall >= 65
    assert "Python" in [s.name for s in result.matched]


def test_implied_skill_gets_partial_credit():
    result = analyse(make(), "We need Deep Learning experience and Python.")
    deep = next(s for s in result.matched + result.missing if s.name == "Deep Learning")
    assert deep.in_resume
    assert deep.evidence == "implied"
    assert 0 < deep.coverage < 100


def test_irrelevant_resume_scores_low():
    chef = make("Summary\nPastry chef.\n\nExperience\nRan a bakery, managed staff.\n")
    assert analyse(chef, JD).overall < 45


def test_empty_job_description_does_not_crash():
    result = analyse(make(), "")
    assert 0 <= result.overall <= 100


@pytest.mark.parametrize("score,word", [(85, "Great"), (70, "Solid"), (55, "Partial"), (20, "Weak")])
def test_verdict_bands(score, word):
    result = analyse(make(), JD)
    result.overall = score
    assert result.verdict.startswith(word)


def test_decorated_headings_are_matched():
    """Real resumes write 'FEATURED PROJECTS', not 'Projects'."""
    text = "FEATURED PROJECTS\nBuilt a scraper.\n\nRELEVANT WORK EXPERIENCE\nInterned at Acme.\n"
    sections = split_sections(text)
    assert "projects" in sections
    assert "experience" in sections


def test_body_text_is_not_mistaken_for_heading():
    text = "Summary\nI have strong skills in data analysis and modern engineering practice.\n"
    sections = split_sections(text)
    assert "skills" not in sections
