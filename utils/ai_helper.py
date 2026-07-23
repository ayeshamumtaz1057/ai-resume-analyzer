"""AI-powered improvement suggestions (Google Gemini).

Design goal: the app works with ZERO configuration (great for a free public
demo), and becomes smarter when a GEMINI_API_KEY is provided.

  * If GEMINI_API_KEY is available (env var, .env file, or Streamlit secrets),
    we ask Gemini for tailored suggestions.
  * Otherwise we fall back to solid rule-based advice from the skill gap.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Load variables from a local .env file if present (ignored in the cloud).
load_dotenv()


def _get_api_key() -> Optional[str]:
    """Fetch the Gemini API key from env or Streamlit secrets, if present."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def _rule_based_suggestions(
    score: float, matched: List[str], missing: List[str]
) -> str:
    """Deterministic advice used when no API key is configured."""
    lines: List[str] = []

    if score >= 75:
        lines.append(
            f"**Strong match ({score:.0f}%).** Your resume aligns well with this "
            "role. Focus on quantifying your impact and tightening the summary."
        )
    elif score >= 50:
        lines.append(
            f"**Moderate match ({score:.0f}%).** You're a plausible candidate, "
            "but the resume could mirror the job's language more closely."
        )
    else:
        lines.append(
            f"**Low match ({score:.0f}%).** Rework the resume around the job's "
            "keywords and highlight the most relevant experience first."
        )

    if missing:
        shown = ", ".join(missing[:8])
        lines.append(
            f"**Skills to add or highlight:** {shown}. If you have real "
            "experience with these, surface them with concrete examples."
        )
    else:
        lines.append(
            "**Skill coverage:** You already cover the key skills detected in "
            "the job description; back each one with evidence."
        )

    if matched:
        lines.append(
            f"**Lead with your strengths:** {', '.join(matched[:6])}. Put these "
            "near the top with measurable results (numbers, %, scale)."
        )

    lines.append(
        "**General tips:** Use action verbs, keep bullets to one line, remove "
        "filler, and tailor the top third of the resume to this job."
    )
    return "\n\n".join(lines)


def _gemini_suggestions(
    api_key: str, resume_text: str, job_text: str, score: float, missing: List[str]
) -> str:
    """Ask Gemini for tailored suggestions. Raises on any API failure."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""You are an expert technical recruiter and resume coach.

The candidate's resume scored {score:.0f}% similarity against this job.
Detected missing skills: {", ".join(missing) or "none"}.

JOB DESCRIPTION:
\"\"\"{job_text[:4000]}\"\"\"

RESUME:
\"\"\"{resume_text[:4000]}\"\"\"

Give concise, actionable feedback in markdown with these sections:
1. **Overall fit** (2-3 sentences)
2. **Top 3 things to fix** (specific bullet points)
3. **Missing keywords worth adding** (only if genuinely relevant)
4. **One rewritten bullet point** showing a stronger, quantified version

Be direct and practical. Do not invent experience the candidate lacks."""

    response = model.generate_content(prompt)
    return (response.text or "").strip()


def generate_suggestions(
    resume_text: str,
    job_text: str,
    score: float,
    skill_gap: Dict[str, List[str]],
) -> str:
    """Return improvement suggestions as markdown.

    Uses Gemini if a key is configured; otherwise rule-based advice.
    Never raises: falls back gracefully on any error.
    """
    matched = skill_gap.get("matched", [])
    missing = skill_gap.get("missing", [])

    api_key = _get_api_key()
    if api_key:
        try:
            return _gemini_suggestions(api_key, resume_text, job_text, score, missing)
        except Exception as exc:  # noqa: BLE001
            fallback = _rule_based_suggestions(score, matched, missing)
            return (
                f"> _AI service unavailable ({exc.__class__.__name__}); "
                "showing rule-based suggestions instead._\n\n" + fallback
            )

    return _rule_based_suggestions(score, matched, missing)
