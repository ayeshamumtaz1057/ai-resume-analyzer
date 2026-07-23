"""AI Resume Analyzer - modern dashboard UI (Streamlit).

Features:
  * Sidebar navigation
  * Dashboard metric cards (Match score, ATS score, Skills matched, Missing)
  * Donut chart + skill bars
  * Strengths vs. Missing skills columns
  * AI suggestions
  * Progress animation, dark mode, responsive layout

Run:  streamlit run app.py
"""

from __future__ import annotations

import time

import streamlit as st

from utils import (
    extract_text_from_pdf,
    compute_similarity,
    compare_skills,
    generate_suggestions,
    compute_ats_score,
    rewrite_bullets,
    generate_cover_letter,
    generate_interview_qa,
    estimate_salary,
    format_salary,
    build_roadmap,
)
from utils.skills import category_of

# --------------------------------------------------------------------------- #
# Page config
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #
for key, default in [
    ("dark", False),
    ("page", "Home"),
    ("results", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# --------------------------------------------------------------------------- #
# Theme / CSS
# --------------------------------------------------------------------------- #
def inject_css(dark: bool) -> None:
    """Inject the design system CSS for light or dark mode."""
    if dark:
        bg, card, text, muted, border = "#0f172a", "#1e293b", "#f1f5f9", "#94a3b8", "#334155"
    else:
        bg, card, text, muted, border = "#f6f8fc", "#ffffff", "#0f172a", "#64748b", "#e2e8f0"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"], .stApp {{
            font-family: 'Inter', -apple-system, sans-serif;
        }}
        .stApp {{ background: {bg}; color: {text}; }}
        section[data-testid="stSidebar"] {{ background: #111827; }}
        section[data-testid="stSidebar"] * {{ color: #e5e7eb !important; }}

        #MainMenu, footer {{ visibility: hidden; }}

        .hero-title {{
            font-size: 2.1rem; font-weight: 800; color: {text};
            text-align: center; margin: 0 0 .2rem 0;
        }}
        .hero-sub {{
            text-align: center; color: {muted}; font-size: .95rem;
            margin-bottom: 1.4rem;
        }}

        .card {{
            background: {card}; border: 1px solid {border}; border-radius: 16px;
            padding: 1.1rem 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,.06);
            transition: transform .18s ease, box-shadow .18s ease;
            height: 100%;
        }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 22px rgba(0,0,0,.10); }}

        .metric-label {{
            font-size: .78rem; font-weight: 600; color: {muted};
            text-transform: uppercase; letter-spacing: .04em;
        }}
        .metric-value {{ font-size: 2rem; font-weight: 800; color: {text}; line-height: 1.1; }}
        .metric-row {{ display: flex; align-items: center; justify-content: space-between; gap: .6rem; }}

        .sec-title {{
            font-size: 1.05rem; font-weight: 700; color: {text};
            margin: 0 0 .7rem 0;
        }}

        .pill {{
            display: inline-flex; align-items: center; gap: .35rem;
            padding: 5px 12px; margin: 3px; border-radius: 999px;
            font-size: .82rem; font-weight: 600;
        }}
        .pill-ok   {{ background: rgba(34,197,94,.14);  color: #16a34a; }}
        .pill-no   {{ background: rgba(239,68,68,.14);  color: #ef4444; }}
        .pill-info {{ background: rgba(99,102,241,.14); color: #6366f1; }}

        .bar-wrap {{ margin-bottom: .75rem; }}
        .bar-top {{
            display: flex; justify-content: space-between;
            font-size: .84rem; font-weight: 600; color: {text}; margin-bottom: 4px;
        }}
        .bar-bg {{ background: {border}; border-radius: 999px; height: 8px; width: 100%; }}
        .bar-fill {{
            height: 8px; border-radius: 999px;
            background: linear-gradient(90deg,#6366f1,#06b6d4);
        }}

        .drop {{
            border: 2px dashed {border}; border-radius: 14px;
            padding: .4rem; text-align: center; color: {muted};
        }}

        div.stButton > button {{
            background: linear-gradient(90deg,#6366f1,#8b5cf6);
            color: #fff; border: none; border-radius: 12px;
            padding: .7rem 1rem; font-weight: 700; font-size: .95rem;
            width: 100%; transition: filter .15s ease, transform .15s ease;
        }}
        div.stButton > button:hover {{ filter: brightness(1.08); transform: translateY(-1px); }}

        .step {{ display: flex; gap: .7rem; margin-bottom: .9rem; }}
        .step-num {{
            min-width: 26px; height: 26px; border-radius: 8px;
            background: rgba(99,102,241,.15); color: #6366f1;
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: .8rem;
        }}
        .step-t {{ font-weight: 700; font-size: .88rem; color: {text}; }}
        .step-d {{ font-size: .8rem; color: {muted}; }}

        @media (max-width: 640px) {{
            .hero-title {{ font-size: 1.5rem; }}
            .metric-value {{ font-size: 1.5rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def donut(pct: float, colour: str, size: int = 74) -> str:
    """Return an SVG donut ring for a percentage."""
    r, sw = size / 2 - 7, 7
    circ = 2 * 3.14159 * r
    filled = circ * (max(0.0, min(pct, 100.0)) / 100)
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none"
              stroke="rgba(148,163,184,.25)" stroke-width="{sw}"/>
      <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none"
              stroke="{colour}" stroke-width="{sw}" stroke-linecap="round"
              stroke-dasharray="{filled} {circ}"
              transform="rotate(-90 {size/2} {size/2})"/>
    </svg>"""


def metric_card(label: str, value: str, pct: float | None, colour: str) -> str:
    """Return HTML for a dashboard metric card."""
    art = donut(pct, colour) if pct is not None else (
        f'<div style="font-size:1.8rem">{"" }</div>'
    )
    return f"""
    <div class="card">
      <div class="metric-row">
        <div>
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
        </div>
        <div>{art}</div>
      </div>
    </div>"""


def skill_bar(name: str, pct: int) -> str:
    """Return HTML for a labelled progress bar."""
    return f"""
    <div class="bar-wrap">
      <div class="bar-top"><span>{name}</span><span>{pct}%</span></div>
      <div class="bar-bg"><div class="bar-fill" style="width:{pct}%"></div></div>
    </div>"""


inject_css(st.session_state.dark)


# --------------------------------------------------------------------------- #
# Sidebar navigation
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown(
        "### AI Resume Analyzer\n"
        "<span style='font-size:.82rem;color:#9ca3af'>Smart AI to analyze your "
        "resume and get hired faster.</span>",
        unsafe_allow_html=True,
    )
    st.write("")

    st.session_state.page = st.radio(
        "Navigation",
        ["Home", "Dashboard", "Resume Analysis", "AI Tools", "Reports",
         "How it Works", "Settings"],
        label_visibility="collapsed",
    )

    st.divider()
    st.session_state.dark = st.toggle("Dark mode", value=st.session_state.dark)
    st.caption("Tip: add a GEMINI_API_KEY in secrets for AI-written suggestions.")


page = st.session_state.page
res = st.session_state.results


# --------------------------------------------------------------------------- #
# HOME - input + analyze
# --------------------------------------------------------------------------- #
if page == "Home":
    st.markdown('<div class="hero-title">AI Resume Analyzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Get AI-powered insights to improve your resume '
        "and match the perfect job.</div>",
        unsafe_allow_html=True,
    )

    # ---- Top metric cards (show last results, or placeholders) ----
    m = res or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        metric_card("Resume Score", f"{m.get('score', 0):.0f}%", m.get("score", 0), "#6366f1"),
        unsafe_allow_html=True,
    )
    c2.markdown(
        metric_card("ATS Score", f"{m.get('ats', 0):.0f}%", m.get("ats", 0), "#22c55e"),
        unsafe_allow_html=True,
    )
    c3.markdown(
        metric_card("Skills Matched", f"{len(m.get('matched', [])):02d}", None, "#6366f1"),
        unsafe_allow_html=True,
    )
    c4.markdown(
        metric_card("Missing Skills", f"{len(m.get('missing', [])):02d}", None, "#f97316"),
        unsafe_allow_html=True,
    )

    st.write("")

    # ---- Inputs ----
    left, right, side = st.columns([1.1, 1.3, 0.9])

    with left:
        st.markdown('<div class="sec-title">Upload Your Resume</div>', unsafe_allow_html=True)
        resume_file = st.file_uploader(
            "Drag & drop your PDF here", type=["pdf"], label_visibility="collapsed"
        )
        st.caption("PDF only  |  Max size 10MB")
        resume_manual = st.text_area(
            "or paste resume text", height=90, placeholder="...or paste resume text"
        )

    with right:
        st.markdown('<div class="sec-title">Job Description</div>', unsafe_allow_html=True)
        job_text = st.text_area(
            "Job description",
            height=232,
            placeholder="We are looking for a Data Analyst who can work with large "
            "datasets, create reports, and generate insights...",
            label_visibility="collapsed",
        )

    with side:
        st.markdown('<div class="sec-title">How it works</div>', unsafe_allow_html=True)
        steps = [
            ("1", "Upload Resume", "Upload your CV in PDF format."),
            ("2", "Paste Job Description", "Add the full job posting details."),
            ("3", "Get AI Insights", "Match score, missing skills & suggestions."),
        ]
        html = "".join(
            f'<div class="step"><div class="step-num">{n}</div>'
            f'<div><div class="step-t">{t}</div><div class="step-d">{d}</div></div></div>'
            for n, t, d in steps
        )
        st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)

    st.write("")
    if st.button("Analyze Resume  →"):
        # Resolve resume text
        resume_text = ""
        if resume_file is not None:
            resume_text = extract_text_from_pdf(resume_file)
        elif resume_manual.strip():
            resume_text = resume_manual

        if not resume_text.strip():
            st.error("Please upload a PDF resume or paste resume text.")
            st.stop()
        if not job_text.strip():
            st.error("Please paste a job description.")
            st.stop()

        # ---- Progress animation ----
        stages = [
            "Uploading resume",
            "Extracting text",
            "Identifying skills",
            "Matching with job description",
            "Generating AI suggestions",
        ]
        bar = st.progress(0)
        status = st.empty()
        for i, stage in enumerate(stages, start=1):
            status.markdown(f"**{stage}...**")
            bar.progress(int(i / len(stages) * 100))
            time.sleep(0.25)

        score = compute_similarity(resume_text, job_text)
        gap = compare_skills(resume_text, job_text)
        ats = compute_ats_score(resume_text, job_text)
        tips = generate_suggestions(resume_text, job_text, score, gap)

        status.empty()
        bar.empty()

        st.session_state.results = {
            "score": score,
            "ats": ats["score"],
            "checks": ats["checks"],
            "matched": gap["matched"],
            "missing": gap["missing"],
            "extra": gap["extra"],
            "tips": tips,
            "resume_text": resume_text,
            "job_text": job_text,
            "file_name": resume_file.name if resume_file else "pasted_text.txt",
        }
        st.session_state.page = "Dashboard"
        st.rerun()


# --------------------------------------------------------------------------- #
# DASHBOARD - results
# --------------------------------------------------------------------------- #
elif page == "Dashboard":
    if not res:
        st.info("No analysis yet. Go to **Home**, add a resume and job description, "
                "then click **Analyze Resume**.")
    else:
        st.markdown('<div class="hero-title">Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">Your latest resume analysis.</div>',
                    unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("Resume Score", f"{res['score']:.0f}%", res["score"], "#6366f1"),
                    unsafe_allow_html=True)
        c2.markdown(metric_card("ATS Score", f"{res['ats']:.0f}%", res["ats"], "#22c55e"),
                    unsafe_allow_html=True)
        c3.markdown(metric_card("Skills Matched", f"{len(res['matched']):02d}", None, "#6366f1"),
                    unsafe_allow_html=True)
        c4.markdown(metric_card("Missing Skills", f"{len(res['missing']):02d}", None, "#f97316"),
                    unsafe_allow_html=True)

        st.write("")
        left, right = st.columns([1, 1.25])

        # ---- Donut + legend ----
        with left:
            total = len(res["matched"]) + len(res["missing"]) or 1
            pct_m = round(len(res["matched"]) / total * 100)
            st.markdown(
                f"""<div class="card" style="text-align:center">
                    <div class="sec-title">Match Score</div>
                    {donut(res['score'], '#6366f1', 150)}
                    <div style="font-size:1.7rem;font-weight:800;margin-top:-96px;
                                margin-bottom:60px">{res['score']:.0f}%</div>
                    <div>
                      <span class="pill pill-ok">Matched {pct_m}%</span>
                      <span class="pill pill-no">Missing {100 - pct_m}%</span>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

        # ---- Top skills bars ----
        with right:
            top = res["matched"][:6] or res["missing"][:6]
            if top:
                step = 90
                bars = ""
                for i, s in enumerate(top):
                    val = max(45, step - i * 8)
                    bars += skill_bar(s.title(), val)
                st.markdown(
                    f'<div class="card"><div class="sec-title">Top Skills</div>{bars}</div>',
                    unsafe_allow_html=True,
                )

        st.write("")
        col_a, col_b = st.columns(2)

        with col_a:
            pills = "".join(f'<span class="pill pill-ok">✓ {s}</span>' for s in res["matched"]) \
                or '<span style="color:#94a3b8">None detected</span>'
            st.markdown(
                f'<div class="card"><div class="sec-title">Strengths</div>{pills}</div>',
                unsafe_allow_html=True,
            )

        with col_b:
            pills = "".join(f'<span class="pill pill-no">✗ {s}</span>' for s in res["missing"]) \
                or '<span style="color:#94a3b8">Nothing missing</span>'
            st.markdown(
                f'<div class="card"><div class="sec-title">Missing Skills</div>{pills}</div>',
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown('<div class="sec-title">AI Suggestions</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(res["tips"])


# --------------------------------------------------------------------------- #
# RESUME ANALYSIS - detail
# --------------------------------------------------------------------------- #
elif page == "Resume Analysis":
    if not res:
        st.info("Run an analysis from **Home** first.")
    else:
        st.markdown('<div class="hero-title">Resume Analysis</div>', unsafe_allow_html=True)
        st.write("")

        st.markdown('<div class="sec-title">ATS Checks</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, chk in enumerate(res["checks"]):
            mark = "✓" if chk["passed"] else "✗"
            cls = "pill-ok" if chk["passed"] else "pill-no"
            cols[i % 3].markdown(
                f'<div class="card" style="margin-bottom:.7rem">'
                f'<span class="pill {cls}">{mark} {chk["label"]}</span>'
                f'<div style="font-size:.82rem;color:#94a3b8;margin-top:.4rem">'
                f'{chk["detail"]}</div></div>',
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown('<div class="sec-title">Job skills by category</div>', unsafe_allow_html=True)
        all_skills = sorted(set(res["matched"] + res["missing"]))
        by_cat: dict[str, list[str]] = {}
        for s in all_skills:
            by_cat.setdefault(category_of(s), []).append(s)
        cats = sorted(by_cat.items())
        cols = st.columns(min(3, len(cats)) or 1)
        for i, (cat, items) in enumerate(cats):
            body = "".join(
                f'<span class="pill {"pill-ok" if s in res["matched"] else "pill-no"}">{s}</span>'
                for s in items
            )
            cols[i % len(cols)].markdown(
                f'<div class="card" style="margin-bottom:.7rem">'
                f'<div class="step-t">{cat}</div>{body}</div>',
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown('<div class="sec-title">Resume Preview</div>',
                    unsafe_allow_html=True)
        text = res["resume_text"]
        per_page = 1800
        pages = max(1, (len(text) + per_page - 1) // per_page)
        pg = st.number_input(
            f"Page (1 of {pages})", min_value=1, max_value=pages, value=1, step=1
        )
        chunk = text[(pg - 1) * per_page: pg * per_page]
        st.markdown(
            f'<div class="card"><div class="step-t">{res.get("file_name", "resume")}'
            f'</div><pre style="white-space:pre-wrap;font-size:.82rem;'
            f'color:#94a3b8;margin-top:.6rem">{chunk}</pre></div>',
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------- #
# AI TOOLS - the 6 extra features
# --------------------------------------------------------------------------- #
elif page == "AI Tools":
    st.markdown('<div class="hero-title">AI Tools</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Six extra tools built on your analysis. They work '
        "without an API key, and get sharper with Gemini enabled.</div>",
        unsafe_allow_html=True,
    )

    if not res:
        st.info("Run an analysis from **Home** first to unlock these tools.")
    else:
        tabs = st.tabs([
            "Resume Rewrite",
            "ATS Checker",
            "Cover Letter",
            "Interview Q&A",
            "Salary Estimator",
            "Learning Roadmap",
        ])

        # ---- 1. AI Resume Rewrite ----
        with tabs[0]:
            st.markdown('<div class="sec-title">AI Resume Rewrite</div>',
                        unsafe_allow_html=True)
            st.caption("Turns weak bullet points into strong, quantified ones.")
            if st.button("Rewrite my bullets", key="rw"):
                with st.spinner("Rewriting..."):
                    st.session_state.rewrite = rewrite_bullets(
                        res["resume_text"], res.get("job_text", "")
                    )
            if st.session_state.get("rewrite"):
                with st.container(border=True):
                    st.markdown(st.session_state.rewrite)

        # ---- 2. ATS Checker ----
        with tabs[1]:
            st.markdown('<div class="sec-title">ATS Checker</div>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(
                    f'''<div class="card" style="text-align:center">
                        {donut(res["ats"], "#22c55e", 130)}
                        <div style="font-size:1.6rem;font-weight:800;
                                    margin-top:-84px;margin-bottom:52px">
                            {res["ats"]:.0f}%</div>
                        <div class="metric-label">ATS Score</div>
                    </div>''',
                    unsafe_allow_html=True,
                )
            with c2:
                rows = ""
                for chk in res["checks"]:
                    mark = "✓" if chk["passed"] else "✗"
                    cls = "pill-ok" if chk["passed"] else "pill-no"
                    rows += (
                        f'<div style="margin-bottom:.5rem">'
                        f'<span class="pill {cls}">{mark} {chk["label"]}</span>'
                        f'<span style="font-size:.82rem;color:#94a3b8;'
                        f'margin-left:.4rem">{chk["detail"]}</span></div>'
                    )
                st.markdown(f'<div class="card">{rows}</div>',
                            unsafe_allow_html=True)

        # ---- 3. Cover Letter ----
        with tabs[2]:
            st.markdown('<div class="sec-title">Cover Letter Generator</div>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            name = c1.text_input("Your name", placeholder="Ayesha Mumtaz")
            company = c2.text_input("Company name", placeholder="DataCorp")
            if st.button("Generate cover letter", key="cl"):
                with st.spinner("Writing..."):
                    st.session_state.cover = generate_cover_letter(
                        res["resume_text"], res.get("job_text", ""), name, company
                    )
            if st.session_state.get("cover"):
                with st.container(border=True):
                    st.markdown(st.session_state.cover)
                st.download_button(
                    "Download letter (.md)",
                    st.session_state.cover,
                    file_name="cover_letter.md",
                )

        # ---- 4. Interview Q&A ----
        with tabs[3]:
            st.markdown('<div class="sec-title">Interview Q&A Generator</div>',
                        unsafe_allow_html=True)
            st.caption("Likely questions for this specific job, with answer hints.")
            if st.button("Generate questions", key="qa"):
                with st.spinner("Preparing questions..."):
                    st.session_state.qa = generate_interview_qa(
                        res["resume_text"], res.get("job_text", "")
                    )
            if st.session_state.get("qa"):
                with st.container(border=True):
                    st.markdown(st.session_state.qa)

        # ---- 5. Salary Estimator ----
        with tabs[4]:
            st.markdown('<div class="sec-title">Salary Estimator</div>',
                        unsafe_allow_html=True)
            est = estimate_salary(res.get("job_text", ""), res["resume_text"])
            c1, c2, c3 = st.columns(3)
            c1.markdown(metric_card("Low", f"{est['low']//1000}k", None, "#6366f1"),
                        unsafe_allow_html=True)
            c2.markdown(metric_card("Typical", f"{est['mid']//1000}k", None, "#22c55e"),
                        unsafe_allow_html=True)
            c3.markdown(metric_card("High", f"{est['high']//1000}k", None, "#f97316"),
                        unsafe_allow_html=True)
            st.write("")
            with st.container(border=True):
                st.markdown(format_salary(est))

        # ---- 6. Learning Roadmap ----
        with tabs[5]:
            st.markdown('<div class="sec-title">Learning Roadmap</div>',
                        unsafe_allow_html=True)
            weeks = st.slider("Plan length (weeks)", 4, 16, 8)
            if st.button("Build my roadmap", key="rm"):
                with st.spinner("Planning..."):
                    st.session_state.roadmap = build_roadmap(res["missing"], weeks)
            if st.session_state.get("roadmap"):
                with st.container(border=True):
                    st.markdown(st.session_state.roadmap)

# --------------------------------------------------------------------------- #
# REPORTS
# --------------------------------------------------------------------------- #
elif page == "Reports":
    if not res:
        st.info("Run an analysis from **Home** first.")
    else:
        st.markdown('<div class="hero-title">Reports</div>', unsafe_allow_html=True)
        report = f"""# AI Resume Analyzer - Report

## Scores
- Match score: {res['score']:.0f}%
- ATS score: {res['ats']:.0f}%
- Skills matched: {len(res['matched'])}
- Skills missing: {len(res['missing'])}

## Matched skills
{", ".join(res['matched']) or "none"}

## Missing skills
{", ".join(res['missing']) or "none"}

## AI suggestions
{res['tips']}
"""
        st.markdown(report)
        st.download_button(
            "Download report (.md)", report, file_name="resume_analysis_report.md"
        )


# --------------------------------------------------------------------------- #
# HOW IT WORKS
# --------------------------------------------------------------------------- #
elif page == "How it Works":
    st.markdown('<div class="hero-title">How it Works</div>', unsafe_allow_html=True)
    st.write("")
    items = [
        ("1", "Extract", "Your PDF resume is converted to plain text with PyPDF2."),
        ("2", "Clean", "Text is tokenized and stop words removed using spaCy."),
        ("3", "Score", "TF-IDF vectors are compared with cosine similarity."),
        ("4", "Compare", "A curated skills database finds matched vs. missing skills."),
        ("5", "Advise", "Gemini generates tailored suggestions (rule-based fallback)."),
    ]
    cols = st.columns(len(items))
    for col, (n, t, d) in zip(cols, items):
        col.markdown(
            f'<div class="card"><div class="step-num">{n}</div>'
            f'<div class="step-t" style="margin-top:.5rem">{t}</div>'
            f'<div class="step-d">{d}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown('<div class="sec-title">Built with</div>', unsafe_allow_html=True)
    tech = ["Python", "Streamlit", "PyPDF2", "spaCy", "scikit-learn", "Gemini API"]
    st.markdown(
        '<div class="card">'
        + "".join(f'<span class="pill pill-info">{t}</span>' for t in tech)
        + "</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# SETTINGS
# --------------------------------------------------------------------------- #
else:
    st.markdown('<div class="hero-title">Settings</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown(
        '<div class="card"><div class="sec-title">AI suggestions</div>'
        '<div class="step-d">The app works without any API key using rule-based '
        "advice. To enable Gemini-written suggestions, add a "
        "<code>GEMINI_API_KEY</code> to your <code>.env</code> file locally, or to "
        "<b>Manage app → Settings → Secrets</b> on Streamlit Cloud.</div></div>",
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Clear current analysis"):
        st.session_state.results = None
        st.success("Cleared.")
