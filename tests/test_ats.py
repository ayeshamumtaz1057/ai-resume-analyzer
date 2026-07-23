"""Tests for ATS scoring."""

from utils.ats import compute_ats_score

GOOD = """
Ayesha Mumtaz
ayesha@email.com | +92 300 1234567 | github.com/ayeshamumtaz1057

Summary
Data analyst with Python and SQL experience.

Experience
Built 3 dashboards that reduced reporting time by 40%.
Developed automated pipelines processing 10000 records daily.
Led a team of 4 students on a analytics project.

Skills
Python, SQL, Pandas, Excel

Education
BS Information Technology
"""


def test_good_resume_scores_high():
    result = compute_ats_score(GOOD, "python sql pandas excel")
    assert result["score"] > 70


def test_empty_resume_scores_zero():
    assert compute_ats_score("")["score"] == 0.0


def test_checks_are_returned():
    result = compute_ats_score(GOOD, "python")
    labels = [c["label"] for c in result["checks"]]
    assert "Contact details" in labels
    assert "Keyword match" in labels
    assert len(result["checks"]) == 6


def test_score_capped_at_100():
    assert compute_ats_score(GOOD * 3, "python sql")["score"] <= 100.0
