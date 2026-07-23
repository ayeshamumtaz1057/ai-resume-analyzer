"""Extra career tools.

Each tool uses Gemini when a GEMINI_API_KEY is configured, and falls back to a
deterministic template-based version so the app is fully usable for free.
"""

from __future__ import annotations

from typing import Dict, List

from .ai_helper import _get_api_key  # reuse key lookup
from .skills import extract_skills

# --------------------------------------------------------------------------- #
# Shared Gemini call
# --------------------------------------------------------------------------- #


def _ask_gemini(prompt: str, max_chars: int = 6000) -> str:
    """Send a prompt to Gemini. Raises if unavailable or on failure."""
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("no api key")

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt[:max_chars])
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("empty response")
    return text


def _try(prompt: str, fallback: str) -> str:
    """Return Gemini's answer, or the fallback if anything goes wrong."""
    try:
        return _ask_gemini(prompt)
    except Exception:
        return fallback


# --------------------------------------------------------------------------- #
# 1. AI Resume Rewrite
# --------------------------------------------------------------------------- #

_STRONG_VERBS = {
    "did": "delivered", "made": "built", "worked on": "developed",
    "helped": "supported", "was responsible for": "led",
    "used": "applied", "did work": "executed",
}


def rewrite_bullets(resume_text: str, job_text: str) -> str:
    """Rewrite weak resume bullets into strong, quantified ones."""
    prompt = f"""You are an expert resume writer.

Rewrite the weakest bullet points from this resume so they are stronger,
quantified, and aligned with the target job. Return markdown with a
"Before / After" pair for 4-5 bullets. Do not invent fake experience -
if a number is unknown, show a placeholder like [X].

TARGET JOB:
\"\"\"{job_text[:2500]}\"\"\"

RESUME:
\"\"\"{resume_text[:3000]}\"\"\""""

    lines = [ln.strip() for ln in resume_text.split("\n") if len(ln.strip()) > 35]
    samples = lines[:4] or ["Worked on data analysis tasks."]

    fb = ["### Suggested rewrites\n"]
    for ln in samples:
        improved = ln
        for weak, strong in _STRONG_VERBS.items():
            if weak in improved.lower():
                improved = improved.lower().replace(weak, f"**{strong}**")
                break
        fb.append(f"**Before:** {ln}\n\n**After:** {improved.capitalize()} "
                  "— achieving [X]% improvement across [Y] items.\n")
    fb.append(
        "\n**Formula to follow:** *Action verb + what you did + tool used + "
        "measurable result.*\n\nExample: *Built an automated reporting pipeline "
        "in Python, cutting manual work by 40%.*"
    )
    return _try(prompt, "\n".join(fb))


# --------------------------------------------------------------------------- #
# 2. Cover Letter Generator
# --------------------------------------------------------------------------- #


def generate_cover_letter(
    resume_text: str, job_text: str, name: str = "", company: str = ""
) -> str:
    """Produce a tailored cover letter."""
    who = name or "[Your Name]"
    firm = company or "[Company Name]"

    prompt = f"""Write a professional cover letter (250-320 words) for this
candidate applying to this job. Use a confident, specific tone. Reference real
skills from the resume only. Address it to {firm}. Sign off as {who}.

JOB:
\"\"\"{job_text[:2500]}\"\"\"

RESUME:
\"\"\"{resume_text[:2500]}\"\"\""""

    skills = extract_skills(resume_text)[:5]
    skill_line = ", ".join(s.title() for s in skills) or "my technical background"

    fb = f"""Dear Hiring Manager at {firm},

I am writing to express my interest in the role described in your posting. After
reviewing the requirements, I believe my background aligns closely with what
your team is looking for.

My core strengths include {skill_line}. In previous work and projects, I have
applied these skills to deliver practical results — building solutions,
analysing data, and collaborating with others to ship work on time. I focus on
writing clear, maintainable code and on understanding the problem before
reaching for a tool.

What draws me to {firm} specifically is the opportunity to work on problems
where careful analysis makes a measurable difference. I am eager to contribute
to your team while continuing to grow as a professional.

I would welcome the chance to discuss how my background could support your
goals. Thank you for your time and consideration.

Sincerely,
{who}

---
*Tip: replace the bracketed fields and add one sentence naming a specific
project or product of the company — it noticeably improves response rates.*"""
    return _try(prompt, fb)


# --------------------------------------------------------------------------- #
# 3. Interview Q&A Generator
# --------------------------------------------------------------------------- #

_GENERIC_QA = [
    ("Tell me about yourself.",
     "Give a 60-second arc: who you are, what you've built, what you want next. "
     "Anchor it to the role."),
    ("Why do you want this role?",
     "Name something specific about the team/product, then link it to a skill "
     "you actually have."),
    ("Describe a challenging problem you solved.",
     "Use STAR: Situation, Task, Action, Result. End with a number if you can."),
    ("What is your biggest weakness?",
     "Pick a real one, then describe the concrete system you use to manage it."),
    ("Where do you see yourself in three years?",
     "Show ambition that fits the role's growth path, not a different career."),
]


def generate_interview_qa(resume_text: str, job_text: str) -> str:
    """Generate likely interview questions with guidance."""
    prompt = f"""Generate 8 likely interview questions for this candidate
applying to this job: a mix of technical (based on the required skills) and
behavioural. After each question, add a 2-sentence hint on how to answer well.
Format as markdown with numbered questions in bold.

JOB:
\"\"\"{job_text[:2500]}\"\"\"

RESUME:
\"\"\"{resume_text[:2000]}\"\"\""""

    job_skills = extract_skills(job_text)[:5]
    fb = ["### Likely interview questions\n"]
    for i, skill in enumerate(job_skills, start=1):
        fb.append(
            f"**{i}. Walk me through a project where you used {skill.title()}.**\n\n"
            f"*Hint:* Describe the goal, your specific role, and the outcome. "
            f"Mention one trade-off you made and why.\n"
        )
    start = len(job_skills)
    for j, (q, hint) in enumerate(_GENERIC_QA, start=start + 1):
        fb.append(f"**{j}. {q}**\n\n*Hint:* {hint}\n")
    return _try(prompt, "\n".join(fb))


# --------------------------------------------------------------------------- #
# 4. Salary Estimator
# --------------------------------------------------------------------------- #

# Rough monthly PKR bands for Pakistan's tech market, used as a transparent
# heuristic. These are illustrative starting points, not market data.
_BASE_PKR = {"junior": 80_000, "mid": 180_000, "senior": 350_000}

_ROLE_MULTIPLIER = {
    "data": 1.05, "machine learning": 1.20, "ai": 1.20, "devops": 1.15,
    "cloud": 1.15, "backend": 1.05, "frontend": 0.95, "qa": 0.85,
    "intern": 0.35,
}


def estimate_salary(job_text: str, resume_text: str = "") -> Dict[str, object]:
    """Return a rough salary band plus the reasoning behind it."""
    lowered = job_text.lower()

    if any(w in lowered for w in ["senior", "lead", "principal", "5+ years"]):
        level = "senior"
    elif any(w in lowered for w in ["junior", "entry", "fresh", "graduate", "intern"]):
        level = "junior"
    else:
        level = "mid"

    multiplier = 1.0
    matched_roles = []
    for keyword, mult in _ROLE_MULTIPLIER.items():
        if keyword in lowered:
            multiplier = max(multiplier, mult) if mult > 1 else min(multiplier, mult)
            matched_roles.append(keyword)

    base = _BASE_PKR[level]
    mid = base * multiplier
    low, high = mid * 0.75, mid * 1.35

    skill_count = len(extract_skills(job_text))

    return {
        "level": level,
        "low": int(low),
        "mid": int(mid),
        "high": int(high),
        "roles": matched_roles,
        "skill_count": skill_count,
    }


def format_salary(est: Dict[str, object]) -> str:
    """Render a salary estimate as markdown."""
    return f"""### Estimated monthly range (PKR)

**PKR {est['low']:,} – {est['high']:,}**  ·  typical: **PKR {est['mid']:,}**

- **Seniority detected:** {str(est['level']).title()}
- **Role signals:** {', '.join(est['roles']) or 'general'}
- **Distinct skills required:** {est['skill_count']}

> ⚠️ This is a rough heuristic based on seniority and role keywords, not live
> market data. Always cross-check with Glassdoor, Levels.fyi, or local job
> boards before negotiating."""


# --------------------------------------------------------------------------- #
# 5. Learning Roadmap
# --------------------------------------------------------------------------- #

_RESOURCES = {
    "python": "Python docs tutorial, Automate the Boring Stuff",
    "sql": "SQLBolt, Mode SQL tutorial",
    "docker": "Docker's official 'Get Started' guide",
    "aws": "AWS Cloud Practitioner Essentials (free)",
    "machine learning": "Andrew Ng's ML course, scikit-learn user guide",
    "deep learning": "fast.ai Practical Deep Learning",
    "tensorflow": "TensorFlow official tutorials",
    "pytorch": "PyTorch 60-minute Blitz",
    "react": "react.dev learn section",
    "git": "Pro Git book (free online)",
    "pandas": "10 minutes to pandas, Kaggle Pandas course",
    "nlp": "spaCy course (free), Hugging Face NLP course",
}


def build_roadmap(missing: List[str], weeks: int = 8) -> str:
    """Build a week-by-week learning plan for the missing skills."""
    if not missing:
        return ("### You're covered ✅\n\nNo missing skills were detected for this "
                "job. Focus on deepening what you already have and adding "
                "measurable results to your resume.")

    prompt = f"""Create a {weeks}-week learning roadmap for someone who needs to
learn these skills: {', '.join(missing[:8])}.
For each week give: the focus skill, one concrete project to build, and one
free resource. Format as markdown with week headings. Be realistic about pace."""

    picks = missing[:min(len(missing), weeks)]
    per = max(1, weeks // max(len(picks), 1))

    fb = [f"### {weeks}-week roadmap\n"]
    week = 1
    for skill in picks:
        end = min(week + per - 1, weeks)
        span = f"Week {week}" if week == end else f"Weeks {week}–{end}"
        resource = _RESOURCES.get(skill, "Official documentation + one YouTube crash course")
        fb.append(
            f"**{span} — {skill.title()}**\n\n"
            f"- *Learn:* core concepts and syntax\n"
            f"- *Build:* a small project that uses {skill} end-to-end\n"
            f"- *Resource:* {resource}\n"
        )
        week = end + 1
        if week > weeks:
            break

    fb.append(
        "\n**How to make it stick:** build something small every week and push it "
        "to GitHub. A visible project beats a certificate on most resumes."
    )
    return _try(prompt, "\n".join(fb))
