"""Find skills in free text.

Primary path uses a spaCy PhraseMatcher (token-aware, so "R" inside "React"
never matches). If the spaCy model is missing we fall back to word-boundary
regex so the app still runs on a fresh clone.
"""

from __future__ import annotations

import re
from functools import lru_cache

from .skills_db import ALL_ALIASES, CANONICAL

_MODEL = "en_core_web_sm"


@lru_cache(maxsize=1)
def _load_matcher():
    """Build the spaCy pipeline + matcher once per process."""
    try:
        import spacy
        from spacy.matcher import PhraseMatcher
    except ImportError:
        return None, None

    try:
        nlp = spacy.load(_MODEL, disable=["ner", "lemmatizer", "textcat"])
    except OSError:
        # Model not downloaded — a blank English pipeline still tokenises fine.
        try:
            import spacy

            nlp = spacy.blank("en")
        except Exception:
            return None, None

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    for alias in ALL_ALIASES:
        matcher.add(CANONICAL[alias], [nlp.make_doc(alias)])
    return nlp, matcher


def _regex_extract(text: str) -> set[str]:
    found = set()
    lowered = text.lower()
    for alias in ALL_ALIASES:
        pattern = r"(?<![\w+#])" + re.escape(alias) + r"(?![\w+#])"
        if re.search(pattern, lowered):
            found.add(CANONICAL[alias])
    return found


def extract_skills(text: str) -> set[str]:
    """Return the set of canonical skill names present in `text`."""
    if not text or not text.strip():
        return set()

    nlp, matcher = _load_matcher()
    if nlp is None:
        return _regex_extract(text)

    doc = nlp(text.lower())
    return {nlp.vocab.strings[match_id] for match_id, _, _ in matcher(doc)}


def skill_frequency(text: str) -> dict[str, int]:
    """How many times each skill appears — used to gauge depth vs. a passing mention."""
    counts: dict[str, int] = {}
    lowered = text.lower()
    for alias in ALL_ALIASES:
        pattern = r"(?<![\w+#])" + re.escape(alias) + r"(?![\w+#])"
        hits = len(re.findall(pattern, lowered))
        if hits:
            name = CANONICAL[alias]
            counts[name] = counts.get(name, 0) + hits
    return counts
