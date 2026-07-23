"""Per-user analysis history.

Stores scores and skill names only — never resume text. Someone who reads the
JSON file learns which skills a job asked for, not the contents of anyone's CV.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .auth import DATA_DIR
from .scorer import Analysis

HISTORY_FILE = DATA_DIR / "history.json"
MAX_ENTRIES = 25  # per user, oldest dropped first


@dataclass
class Entry:
    timestamp: str
    filename: str
    job_title: str
    overall: int
    verdict: str
    skill_coverage: int
    similarity: int
    quality: int
    matched: list[str]
    missing: list[str]


def _load() -> dict[str, list[dict]]:
    if not HISTORY_FILE.exists():
        return {}
    try:
        return json.loads(HISTORY_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(HISTORY_FILE)


def _guess_title(job_description: str) -> str:
    """First plausible role phrase in the posting, for labelling the entry."""
    head = " ".join(job_description.split())[:120]
    for marker in ("Intern", "Engineer", "Scientist", "Analyst", "Developer", "Manager"):
        idx = head.find(marker)
        if idx != -1:
            start = max(0, head.rfind(".", 0, idx) + 1)
            return head[start : idx + len(marker)].strip(" ,.-") or marker
    return head[:40] + ("…" if len(head) > 40 else "")


def add(email: str, analysis: Analysis, filename: str, job_description: str) -> None:
    entry = Entry(
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        filename=filename,
        job_title=_guess_title(job_description),
        overall=analysis.overall,
        verdict=analysis.verdict,
        skill_coverage=analysis.skill_coverage,
        similarity=analysis.similarity,
        quality=analysis.quality,
        matched=[s.name for s in analysis.matched],
        missing=[s.name for s in analysis.missing],
    )
    data = _load()
    entries = data.setdefault(email.lower(), [])
    entries.insert(0, asdict(entry))
    data[email.lower()] = entries[:MAX_ENTRIES]
    _save(data)


def list_for(email: str) -> list[dict]:
    return _load().get(email.lower(), [])


def clear(email: str) -> None:
    data = _load()
    data.pop(email.lower(), None)
    _save(data)


def trend(email: str) -> tuple[int, int] | None:
    """(oldest, newest) overall score — shows whether resume edits are working."""
    entries = list_for(email)
    if len(entries) < 2:
        return None
    return entries[-1]["overall"], entries[0]["overall"]
