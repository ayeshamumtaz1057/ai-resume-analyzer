"""Tests for skill extraction and comparison."""

from utils.skills import extract_skills, compare_skills, category_of


def test_extract_basic_skills():
    text = "Experienced in Python, SQL and Machine Learning."
    skills = extract_skills(text)
    assert "python" in skills
    assert "sql" in skills
    assert "machine learning" in skills


def test_boundary_matching_no_false_positive():
    # "r" should not be matched inside "learn" or "great"
    text = "I am a great learner"
    assert "r" not in extract_skills(text)


def test_special_char_skills():
    skills = extract_skills("Strong in C++ and C# and Node.js")
    assert "c++" in skills
    assert "c#" in skills
    assert "node.js" in skills


def test_compare_skills_gap():
    resume = "python pandas sql"
    job = "python tensorflow docker sql"
    gap = compare_skills(resume, job)
    assert "python" in gap["matched"]
    assert "sql" in gap["matched"]
    assert "tensorflow" in gap["missing"]
    assert "docker" in gap["missing"]


def test_category_lookup():
    assert category_of("python") == "Programming Languages"
    assert category_of("nonexistent-skill") == "Other"
