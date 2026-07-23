"""Text preprocessing utilities (spaCy).

Uses a BLANK spaCy English pipeline (spacy.blank("en")) for tokenization and
spaCy's built-in English STOP_WORDS. This needs NO model download
(no en_core_web_sm), which keeps cloud deployment fast and reliable.
"""

from __future__ import annotations

import re
from typing import List

import spacy
from spacy.lang.en.stop_words import STOP_WORDS

# Blank pipeline = tokenizer only, no downloaded model required.
_nlp = spacy.blank("en")

# Keep common tech tokens intact instead of letting spaCy split them
# (e.g. "c#" -> ["c", "#"]).
_SPECIAL_TOKENS = ["c++", "c#", "f#", "node.js", "asp.net", ".net"]
for _tok in _SPECIAL_TOKENS:
    _nlp.tokenizer.add_special_case(_tok, [{"ORTH": _tok}])


def clean_text(text: str, remove_stopwords: bool = True) -> str:
    """Lowercase, strip punctuation/symbols, remove stopwords, collapse spaces.

    Tech tokens like c++, c#, node.js are preserved.
    """
    if not text:
        return ""

    text = text.lower()
    # Keep letters, digits, spaces, +, # and . so tech terms survive.
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = [t.text for t in _nlp(text)]
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOP_WORDS and t.strip()]

    return " ".join(tokens).strip()


def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
    """Return a list of cleaned tokens from ``text``."""
    cleaned = clean_text(text, remove_stopwords=remove_stopwords)
    return cleaned.split() if cleaned else []
