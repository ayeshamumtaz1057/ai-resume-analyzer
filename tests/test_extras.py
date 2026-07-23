"""Tests for the extra career tools (fallback paths, no API key needed)."""

from utils.extras import (
    build_roadmap,
    estimate_salary,
    format_salary,
    generate_cover_letter,
    generate_interview_qa,
    rewrite_bullets,
)

RESUME = "Worked on data analysis using Python and SQL. Helped build dashboards."
JOB = "Junior Data Analyst. Required: Python, SQL, Excel, Docker, AWS."


def test_rewrite_returns_text():
    out = rewrite_bullets(RESUME, JOB)
    assert isinstance(out, str) and len(out) > 50


def test_cover_letter_includes_names():
    out = generate_cover_letter(RESUME, JOB, "Ayesha", "DataCorp")
    assert "Ayesha" in out or "DataCorp" in out


def test_interview_qa_has_questions():
    out = generate_interview_qa(RESUME, JOB)
    assert "?" in out


def test_salary_detects_seniority():
    senior = estimate_salary("Senior engineer with 5+ years experience")
    junior = estimate_salary("Junior developer, entry level, fresh graduate")
    assert senior["mid"] > junior["mid"]
    assert senior["level"] == "senior"
    assert junior["level"] == "junior"


def test_salary_format_renders():
    out = format_salary(estimate_salary(JOB))
    assert "PKR" in out


def test_roadmap_with_missing_skills():
    out = build_roadmap(["docker", "aws"], weeks=8)
    assert "docker" in out.lower()


def test_roadmap_when_nothing_missing():
    out = build_roadmap([])
    assert "covered" in out.lower()
