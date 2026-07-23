"""Tests for text preprocessing."""

from utils.preprocess import clean_text, tokenize


def test_clean_text_lowercases_and_strips_symbols():
    assert clean_text("Hello, WORLD!!!", remove_stopwords=False) == "hello world"


def test_clean_text_preserves_tech_tokens():
    out = clean_text("C++ and Node.js and C#", remove_stopwords=True)
    assert "c++" in out
    assert "node.js" in out
    assert "c#" in out


def test_clean_text_removes_stopwords():
    out = clean_text("this is a python developer", remove_stopwords=True)
    assert "this" not in out.split()
    assert "python" in out.split()


def test_tokenize_returns_list():
    tokens = tokenize("Python developer with SQL")
    assert isinstance(tokens, list)
    assert "python" in tokens


def test_empty_input():
    assert clean_text("") == ""
    assert tokenize("") == []
