"""Run with: pytest -q"""

import pytest

from core import auth, history
from core.parser import ParsedResume, split_sections
from core.scorer import analyse


@pytest.fixture(autouse=True)
def temp_store(tmp_path, monkeypatch):
    """Point every test at a throwaway data directory."""
    monkeypatch.setattr(auth, "DATA_DIR", tmp_path)
    monkeypatch.setattr(auth, "USERS_FILE", tmp_path / "users.json")
    monkeypatch.setattr(history, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(history, "DATA_DIR", tmp_path)


def test_signup_then_signin():
    auth.sign_up("A@Example.com ", "Ayesha", "correct horse", "correct horse")
    user = auth.sign_in("a@example.com", "correct horse")
    assert user.name == "Ayesha"
    assert user.email == "a@example.com"  # normalised


def test_password_is_never_stored_in_plaintext():
    auth.sign_up("b@example.com", "B", "hunter2hunter2", "hunter2hunter2")
    raw = (auth.USERS_FILE).read_text()
    assert "hunter2hunter2" not in raw


def test_same_password_gets_different_hashes():
    """Per-user salt: identical passwords must not produce identical hashes."""
    auth.sign_up("c@example.com", "C", "samepassword", "samepassword")
    auth.sign_up("d@example.com", "D", "samepassword", "samepassword")
    users = auth._load()
    assert users["c@example.com"]["hash"] != users["d@example.com"]["hash"]


def test_wrong_password_rejected():
    auth.sign_up("e@example.com", "E", "rightpassword", "rightpassword")
    with pytest.raises(auth.AuthError):
        auth.sign_in("e@example.com", "wrongpassword")


def test_unknown_and_wrong_password_give_identical_message():
    """The form must not reveal which emails have accounts."""
    auth.sign_up("f@example.com", "F", "rightpassword", "rightpassword")
    with pytest.raises(auth.AuthError) as known:
        auth.sign_in("f@example.com", "nope12345")
    with pytest.raises(auth.AuthError) as unknown:
        auth.sign_in("ghost@example.com", "nope12345")
    assert str(known.value) == str(unknown.value)


def test_duplicate_email_rejected():
    auth.sign_up("g@example.com", "G", "password123", "password123")
    with pytest.raises(auth.AuthError):
        auth.sign_up("g@example.com", "G2", "password123", "password123")


@pytest.mark.parametrize("email", ["notanemail", "a@b", "@example.com", ""])
def test_invalid_emails_rejected(email):
    with pytest.raises(auth.AuthError):
        auth.sign_up(email, "X", "password123", "password123")


def test_short_and_mismatched_passwords_rejected():
    with pytest.raises(auth.AuthError):
        auth.sign_up("h@example.com", "H", "short", "short")
    with pytest.raises(auth.AuthError):
        auth.sign_up("i@example.com", "I", "password123", "password124")


def test_history_stores_scores_but_not_resume_text():
    text = "Summary\nSecret personal detail here.\n\nSkills\nPython, SQL\n"
    resume = ParsedResume(raw_text=text, sections=split_sections(text), page_count=1)
    result = analyse(resume, "We need Python and SQL.")
    history.add("j@example.com", result, "cv.pdf", "Data Analyst role needing Python and SQL.")

    entries = history.list_for("j@example.com")
    assert len(entries) == 1
    assert entries[0]["overall"] == result.overall
    assert "Secret personal detail" not in history.HISTORY_FILE.read_text()


def test_history_is_per_user():
    text = "Skills\nPython\n"
    resume = ParsedResume(raw_text=text, sections=split_sections(text), page_count=1)
    result = analyse(resume, "We need Python.")
    history.add("k@example.com", result, "a.pdf", "Python Developer")
    assert history.list_for("l@example.com") == []
