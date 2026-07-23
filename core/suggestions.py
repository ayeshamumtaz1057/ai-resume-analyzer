"""Improvement suggestions.

Uses Google Gemini when an API key is configured. Without a key the app still
works: `_fallback` produces rule-based advice from the same analysis object, so
a reviewer cloning the repo sees a full demo on first run.
"""

from __future__ import annotations

import json
import os
import textwrap

from .scorer import Analysis

# Google retires model IDs on a schedule (2.0 Flash was shut down 1 Jun 2026 and
# now 404s), so we try current models in order rather than pinning one that will
# silently die months after this repo was last touched.
MODEL_CANDIDATES = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite"]

PROMPT = textwrap.dedent(
    """
    You are a technical recruiter reviewing a resume against one job description.

    Job description:
    ---
    {jd}
    ---

    Resume text:
    ---
    {resume}
    ---

    Skills the job asks for that the resume does not evidence: {missing}
    Skills present in both: {matched}

    Write 5 to 7 improvement suggestions. Rules:
    - Each is one sentence, imperative, under 22 words.
    - Be specific to this resume. No generic advice like "tailor your resume".
    - Where a skill is missing, say concretely how to show it (a project, a metric, a certification).
    - At least one suggestion must be about quantifying impact with numbers.

    Return ONLY a JSON array of strings. No markdown, no preamble.
    """
).strip()


def _fallback(analysis: Analysis) -> list[str]:
    tips: list[str] = []
    missing = [s.name for s in analysis.missing]

    if missing[:2]:
        tips.append(
            f"Add a project that demonstrably uses {' and '.join(missing[:2])}, with the outcome stated."
        )
    for skill in missing[2:5]:
        tips.append(f"Show hands-on {skill} work — a repo link, a course, or a line in an existing role.")

    thin = [s.name for s in analysis.matched if s.coverage < 60]
    if thin:
        tips.append(
            f"{thin[0]} appears only in passing — back it up in your experience bullets, not just the skills list."
        )

    weakest = min(analysis.section_scores, key=analysis.section_scores.get)
    tips.append(f"Strengthen your {weakest} section; it scores lowest at {analysis.section_scores[weakest]}%.")
    tips.append("Quantify results — replace 'improved model performance' with the accuracy or time saved.")

    if analysis.similarity < 25:
        tips.append("Mirror the job description's own vocabulary so keyword filters read your resume correctly.")

    return tips[:7]


def generate(analysis: Analysis, resume_text: str, job_description: str) -> tuple[list[str], str]:
    """Return (suggestions, source).

    `source` is "gemini" on success, otherwise a short reason the caller can
    show the user — a silent fallback is indistinguishable from a bug.
    """
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        return _fallback(analysis), "no API key set"

    try:
        from google import genai
    except ImportError:
        return _fallback(analysis), "google-genai not installed"

    prompt = PROMPT.format(
        jd=job_description[:6000],
        resume=resume_text[:12000],
        missing=", ".join(s.name for s in analysis.missing) or "none",
        matched=", ".join(s.name for s in analysis.matched) or "none",
    )

    models = [os.getenv("GEMINI_MODEL")] if os.getenv("GEMINI_MODEL") else MODEL_CANDIDATES
    last_error = "unknown error"

    for model in models:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(model=model, contents=prompt)
            raw = (response.text or "").strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            items = json.loads(raw)
            cleaned = [str(i).strip() for i in items if str(i).strip()]
            if cleaned:
                return cleaned[:7], "gemini"
            last_error = f"{model} returned nothing usable"
        except json.JSONDecodeError:
            last_error = f"{model} returned malformed JSON"
        except Exception as exc:
            message = str(exc)
            # A retired or misspelled model ID 404s — worth trying the next one.
            if "404" in message or "not found" in message.lower():
                last_error = f"{model} is unavailable (404)"
                continue
            if "401" in message or "API key" in message or "PERMISSION" in message.upper():
                return _fallback(analysis), "API key rejected"
            if "429" in message or "quota" in message.lower():
                return _fallback(analysis), "quota exceeded"
            last_error = f"{model}: {message[:90]}"

    return _fallback(analysis), last_error
