"""Local account storage with salted password hashing.

Deliberately dependency-free: PBKDF2 ships in the standard library, so the app
adds no auth dependency and no external service. The trade-off is that user data
lives in a JSON file — see `STORAGE_WARNING` and the README before treating this
as production auth.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.getenv("APP_DATA_DIR", "data"))
USERS_FILE = DATA_DIR / "users.json"

# PBKDF2 iteration count. OWASP's floor for SHA-256 is 600k as of 2023.
ITERATIONS = 600_000
MIN_PASSWORD = 8

STORAGE_WARNING = (
    "Accounts are stored in a local JSON file. On Streamlit Cloud the filesystem "
    "is ephemeral, so accounts reset when the app restarts. Do not reuse a real password."
)

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE)


class AuthError(Exception):
    """Raised with a message intended to be shown directly to the user."""


@dataclass
class User:
    email: str
    name: str
    created_at: str


def _load() -> dict:
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(users: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = USERS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(users, indent=2))
    tmp.replace(USERS_FILE)  # atomic, so a crash mid-write cannot truncate the file


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS)
    return digest.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(password, salt)
    # Constant-time compare: a plain == leaks timing information.
    return hmac.compare_digest(candidate, stored_hash)


def sign_up(email: str, name: str, password: str, confirm: str) -> User:
    email = email.strip().lower()
    name = name.strip()

    if not _EMAIL.match(email):
        raise AuthError("Enter a valid email address.")
    if not name:
        raise AuthError("Enter your name.")
    if len(password) < MIN_PASSWORD:
        raise AuthError(f"Password must be at least {MIN_PASSWORD} characters.")
    if password != confirm:
        raise AuthError("Passwords do not match.")

    users = _load()
    if email in users:
        raise AuthError("An account with that email already exists. Sign in instead.")

    digest, salt = hash_password(password)
    users[email] = {
        "name": name,
        "hash": digest,
        "salt": salt,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save(users)
    return User(email=email, name=name, created_at=users[email]["created_at"])


def sign_in(email: str, password: str) -> User:
    email = email.strip().lower()
    record = _load().get(email)

    # Same message either way, so the form cannot be used to discover which
    # emails have accounts.
    if not record or not verify_password(password, record["hash"], record["salt"]):
        raise AuthError("Incorrect email or password.")

    return User(email=email, name=record["name"], created_at=record["created_at"])


def change_password(email: str, current: str, new: str, confirm: str) -> None:
    users = _load()
    record = users.get(email.lower())
    if not record or not verify_password(current, record["hash"], record["salt"]):
        raise AuthError("Current password is incorrect.")
    if len(new) < MIN_PASSWORD:
        raise AuthError(f"Password must be at least {MIN_PASSWORD} characters.")
    if new != confirm:
        raise AuthError("New passwords do not match.")

    digest, salt = hash_password(new)
    record.update(hash=digest, salt=salt)
    _save(users)


def delete_account(email: str) -> None:
    users = _load()
    users.pop(email.lower(), None)
    _save(users)
