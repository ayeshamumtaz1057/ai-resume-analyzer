"""Tests for similarity scoring."""

from utils.similarity import compute_similarity


def test_identical_text_high_score():
    text = "python machine learning data analysis sql"
    assert compute_similarity(text, text) > 99.0


def test_unrelated_text_low_score():
    a = "python machine learning tensorflow"
    b = "chef cooking pasta italian cuisine restaurant"
    assert compute_similarity(a, b) < 20.0


def test_partial_overlap_mid_score():
    resume = "python sql data analysis pandas"
    job = "python data engineering spark hadoop"
    score = compute_similarity(resume, job)
    assert 0.0 < score < 100.0


def test_empty_returns_zero():
    assert compute_similarity("", "python") == 0.0
    assert compute_similarity("python", "") == 0.0
