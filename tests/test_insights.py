"""Tests for experience match, priority and partial matches."""

from utils.insights import (
    experience_match,
    prioritise_missing,
    partial_matches,
    overall_strength,
)

RESUME = "Data Analyst 2021 - 2024. Python, SQL, Pandas used daily. Python again."
JOB = ("Junior Data Analyst. Required: 2+ years experience with Python and SQL. "
       "Docker is required. AWS is nice to have.")


def test_experience_rating_range():
    exp = experience_match(RESUME, JOB)
    assert 0 <= exp["rating"] <= 5
    assert exp["label"] in {"Good Match", "Fair Match", "Below Requirement"}


def test_experience_detects_years():
    exp = experience_match(RESUME, JOB)
    assert exp["required"] == 2
    assert exp["held"] >= 3


def test_priority_high_for_required():
    prio = dict(prioritise_missing(["docker", "aws"], JOB))
    assert prio["docker"] == "High"
    assert prio["aws"] == "Low"


def test_priority_sorted_high_first():
    result = prioritise_missing(["aws", "docker"], JOB)
    assert result[0][1] == "High"


def test_partial_matches_finds_single_mentions():
    partial = partial_matches(RESUME, JOB)
    assert "sql" in partial      # mentioned once
    assert "python" not in partial  # mentioned twice


def test_overall_strength_labels():
    assert overall_strength(90, 90, 5.0)["label"] == "Excellent"
    assert overall_strength(10, 10, 0.0)["label"] == "Needs Work"
