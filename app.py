"""AI Resume Analyzer - dark dashboard UI (Streamlit).

Matches the reference design: metric cards, donut overview, priority badges,
score history, resume preview, AI suggestions, and a bottom stats bar.

Run:  streamlit run app.py
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

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
    experience_match,
    prioritise_missing,
    partial_matches,
    overall_strength,
)
from utils.skills import category_of

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #
_DEFAULTS = {
    "dark": True,
    "page": "Dashboard",
    "results": None,
    "history": [],          # list of (date, score)
    "stats": {"resumes": 0, "jobs": 0, "reports": 0, "interviews": 0},
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# --------------------------------------------------------------------------- #
# Theme
# --------------------------------------------------------------------------- #
def inject_css(dark: bool) -> None:
    if dark:
        bg = "#0b1020"; card = "#111834"; text = "#e8ecf8"
        muted = "#8b95b5"; border = "#1f2a4d"; side = "#0a0f1f"
    else:
        bg = "#f4f6fb"; card = "#ffffff"; text = "#0f172a"
        muted = "#64748b"; border = "#e2e8f0"; side = "#0a0f1f"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {{ font-family:'Inter',sans-serif; }}
    .stApp {{ background:{bg}; color:{text}; }}
    section[data-testid="stSidebar"] {{ background:{side}; border-right:1px solid {border}; }}
    section[data-testid="stSidebar"] * {{ color:#cbd5e1 !important; }}
    #MainMenu, footer, header {{ visibility:hidden; }}
    .block-container {{ padding-top:1.6rem; padding-bottom:1rem; }}

    .brand {{ font-size:2.05rem; font-weight:800;
        background:linear-gradient(90deg,#a78bfa,#8b5cf6,#6366f1);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        margin:0; letter-spacing:-.5px; }}
    .brand-sub {{ color:{muted}; font-size:.9rem; margin:.15rem 0 1.1rem 0; }}

    .card {{ background:{card}; border:1px solid {border}; border-radius:16px;
        padding:1rem 1.15rem; height:100%;
        transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; }}
    .card:hover {{ transform:translateY(-3px); border-color:#8b5cf6;
        box-shadow:0 10px 26px rgba(139,92,246,.18); }}

    .m-label {{ font-size:.82rem; font-weight:600; color:{text}; opacity:.85; }}
    .m-value {{ font-size:1.85rem; font-weight:800; color:{text}; line-height:1.15; }}
    .m-sub {{ font-size:.74rem; color:{muted}; margin-top:.15rem; }}
    .m-row {{ display:flex; align-items:flex-start; justify-content:space-between; gap:.5rem; }}
    .dot {{ height:7px; width:7px; border-radius:50%; display:inline-block; margin-right:5px; }}

    .icon-box {{ width:44px; height:44px; border-radius:12px;
        display:flex; align-items:center; justify-content:center; font-size:1.15rem; }}

    .sec {{ font-size:1rem; font-weight:700; color:{text}; margin:0 0 .8rem 0; }}

    .pill {{ display:inline-block; padding:4px 11px; margin:3px;
        border-radius:999px; font-size:.78rem; font-weight:600; }}
    .p-ok {{ background:rgba(34,197,94,.15); color:#4ade80; }}
    .p-no {{ background:rgba(239,68,68,.15); color:#f87171; }}
    .p-mid {{ background:rgba(251,146,60,.15); color:#fb923c; }}
    .p-info {{ background:rgba(139,92,246,.15); color:#a78bfa; }}

    .badge-high {{ background:rgba(239,68,68,.15); color:#f87171;
        padding:3px 10px; border-radius:7px; font-size:.7rem; font-weight:700; }}
    .badge-med {{ background:rgba(251,146,60,.15); color:#fb923c;
        padding:3px 10px; border-radius:7px; font-size:.7rem; font-weight:700; }}
    .badge-low {{ background:rgba(148,163,184,.15); color:#94a3b8;
        padding:3px 10px; border-radius:7px; font-size:.7rem; font-weight:700; }}

    .bar-w {{ margin-bottom:.65rem; }}
    .bar-t {{ display:flex; justify-content:space-between; align-items:center;
        font-size:.8rem; font-weight:600; color:{text}; margin-bottom:5px; }}
    .bar-bg {{ background:{border}; border-radius:999px; height:7px; width:100%; }}
    .bar-f {{ height:7px; border-radius:999px; }}
    .f-green {{ background:linear-gradient(90deg,#22c55e,#4ade80); }}
    .f-orange {{ background:linear-gradient(90deg,#f97316,#fb923c); }}

    .sug {{ display:flex; align-items:center; gap:.6rem; padding:.55rem 0;
        border-bottom:1px solid {border}; font-size:.84rem; color:{text}; }}
    .sug:last-child {{ border-bottom:none; }}
    .sug-i {{ font-size:1rem; }}
    .chev {{ margin-left:auto; color:{muted}; }}

    .step {{ display:flex; gap:.65rem; margin-bottom:.85rem; align-items:flex-start; }}
    .step-n {{ min-width:25px; height:25px; border-radius:8px;
        background:rgba(139,92,246,.18); color:#a78bfa; display:flex;
        align-items:center; justify-content:center; font-weight:700; font-size:.75rem; }}
    .step-t {{ font-weight:700; font-size:.83rem; color:{text}; }}
    .step-d {{ font-size:.75rem; color:{muted}; }}

    .strength {{ background:linear-gradient(135deg,rgba(139,92,246,.22),rgba(99,102,241,.10));
        border:1px solid rgba(139,92,246,.35); border-radius:16px; padding:1rem 1.15rem; }}

    .statbar {{ background:{card}; border:1px solid {border}; border-radius:16px;
        padding:.9rem 1.1rem; margin-top:1.1rem; }}
    .stat-v {{ font-size:1.25rem; font-weight:800; color:{text}; }}
    .stat-l {{ font-size:.72rem; color:{muted}; }}

    div.stButton > button {{ background:linear-gradient(90deg,#7c3aed,#8b5cf6,#6366f1);
        color:#fff; border:none; border-radius:12px; padding:.72rem 1rem;
        font-weight:700; font-size:.92rem; width:100%;
        transition:filter .15s ease, transform .15s ease; }}
    div.stButton > button:hover {{ filter:brightness(1.12); transform:translateY(-1px); }}

    .stTextArea textarea, .stTextInput input {{
        background:{card} !important; color:{text} !important;
        border:1px solid {border} !important; border-radius:12px !important; }}
    [data-testid="stFileUploader"] section {{
        background:{card}; border:2px dashed rgba(139,92,246,.45);
        border-radius:14px; }}


    /* --- Animated progress bars --- */
    @keyframes grow {{ from {{ width:0 }} }}
    .bar-f {{ animation: grow .9s cubic-bezier(.22,.9,.3,1); }}
    @keyframes ringIn {{ from {{ stroke-dasharray:0 999 }} }}
    .ring-anim {{ animation: ringIn 1.1s cubic-bezier(.22,.9,.3,1); }}
    @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(8px) }} }}
    .card, .strength, .statbar {{ animation: fadeUp .45s ease both; }}

    /* --- Clickable cards --- */
    .card {{ cursor:default; }}
    .card.click:hover {{ cursor:pointer; border-color:#a78bfa; }}

    /* --- Chart tooltips --- */
    .tip {{ position:relative; }}
    svg .hot:hover ~ text {{ font-weight:800; }}

    /* --- Search bar --- */
    .search {{ background:{card}; border:1px solid {border}; border-radius:12px;
        padding:.5rem .85rem; color:{muted}; font-size:.82rem; }}

    /* --- Profile chip --- */
    .prof {{ display:flex; align-items:center; gap:.55rem; background:{card};
        border:1px solid {border}; border-radius:12px; padding:.4rem .7rem; }}
    .prof-av {{ width:30px; height:30px; border-radius:50%;
        background:linear-gradient(135deg,#8b5cf6,#6366f1); display:flex;
        align-items:center; justify-content:center; font-size:.75rem;
        font-weight:800; color:#fff; }}
    .prof-n {{ font-size:.8rem; font-weight:700; color:{text}; line-height:1.1; }}
    .prof-p {{ font-size:.68rem; color:#a78bfa; font-weight:600; }}

    /* --- Footer --- */
    .foot {{ border-top:1px solid {border}; margin-top:1.3rem; padding:.9rem 0;
        text-align:center; font-size:.76rem; color:{muted}; }}
    .foot a {{ color:{muted}; text-decoration:none; margin:0 .35rem; }}
    .foot a:hover {{ color:#a78bfa; }}

    @media (max-width:640px) {{
        .brand {{ font-size:1.45rem; }} .m-value {{ font-size:1.4rem; }}
    }}
    </style>""", unsafe_allow_html=True)


def ring(pct: float, colour: str, size: int = 56, sw: int = 7) -> str:
    r = size / 2 - sw
    circ = 2 * 3.14159 * r
    fill = circ * (max(0.0, min(pct, 100.0)) / 100)
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" '
            f'stroke="rgba(148,163,184,.22)" stroke-width="{sw}"/>'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{colour}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-dasharray="{fill} {circ}" '
            f'class="ring-anim" transform="rotate(-90 {size/2} {size/2})">'
            f'<title>{pct:.0f}%</title></circle></svg>')


def icon_box(emoji: str, colour: str) -> str:
    return (f'<div class="icon-box" style="background:{colour}22;color:{colour}">'
            f'{emoji}</div>')


def metric(label, value, sub, sub_colour, art) -> str:
    return (f'<div class="card"><div class="m-row"><div>'
            f'<div class="m-label">{label}</div>'
            f'<div class="m-value">{value}</div>'
            f'<div class="m-sub"><span class="dot" style="background:{sub_colour}"></span>'
            f'{sub}</div></div><div>{art}</div></div></div>')


def bar(name: str, pct: int, cls: str = "f-green", badge: str = "",
        tip: str = "") -> str:
    """Animated progress bar with a hover tooltip."""
    right = badge or f"{pct}%"
    hint = tip or f"{name}: {pct}%"
    return (f'<div class="bar-w" title="{hint}"><div class="bar-t"><span>{name}</span>'
            f'<span>{right}</span></div><div class="bar-bg">'
            f'<div class="bar-f {cls}" style="width:{pct}%"></div></div></div>')


def line_chart(points: list, text: str, muted: str) -> str:
    """Simple SVG line chart for score history."""
    if len(points) < 2:
        return ('<div style="color:#8b95b5;font-size:.82rem;padding:1.5rem 0;'
                'text-align:center">Run more analyses to build history.</div>')
    w, h, pad = 520, 150, 26
    vals = [p[1] for p in points]
    n = len(vals)
    step = (w - pad * 2) / max(n - 1, 1)
    coords = [(pad + i * step, h - pad - (v / 100) * (h - pad * 2))
              for i, v in enumerate(vals)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.0f},{y:.0f}"
                    for i, (x, y) in enumerate(coords))
    area = path + f" L{coords[-1][0]:.0f},{h-pad} L{pad},{h-pad} Z"
    dots = "".join(
        f'<circle class="hot" cx="{x:.0f}" cy="{y:.0f}" r="5" fill="#a78bfa" '
        f'style="cursor:pointer"><title>{points[i][0]}: {vals[i]:.0f}%</title>'
        f'</circle>' for i, (x, y) in enumerate(coords))
    labels = "".join(
        f'<text x="{x:.0f}" y="{y-9:.0f}" fill="{text}" font-size="9" '
        f'text-anchor="middle">{v:.0f}%</text>'
        for (x, y), v in zip(coords, vals))
    dates = "".join(
        f'<text x="{x:.0f}" y="{h-8}" fill="{muted}" font-size="8" '
        f'text-anchor="middle">{points[i][0]}</text>'
        for i, (x, _) in enumerate(coords))
    return (f'<svg width="100%" viewBox="0 0 {w} {h}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="#8b5cf6" stop-opacity=".35"/>'
            f'<stop offset="100%" stop-color="#8b5cf6" stop-opacity="0"/>'
            f'</linearGradient></defs>'
            f'<path d="{area}" fill="url(#g)"/>'
            f'<path d="{path}" fill="none" stroke="#a78bfa" stroke-width="2.2"/>'
            f'{dots}{labels}{dates}</svg>')


inject_css(st.session_state.dark)
MUTED = "#8b95b5" if st.session_state.dark else "#64748b"
TXT = "#e8ecf8" if st.session_state.dark else "#0f172a"

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown(
        '<div style="display:flex;gap:.6rem;align-items:center;margin-bottom:.4rem">'
        '<svg width="36" height="36" viewBox="0 0 44 44" fill="none"><line x1="22" y1="4" x2="22" y2="10" stroke="#a78bfa" stroke-width="2.2" stroke-linecap="round"/><circle cx="22" cy="4" r="2.6" fill="#4ade80"/><rect x="7" y="10" width="30" height="24" rx="8" fill="#8b5cf6" fill-opacity=".18" stroke="#a78bfa" stroke-width="2.2"/><circle cx="16" cy="20" r="3.2" fill="#a78bfa"/><circle cx="28" cy="20" r="3.2" fill="#a78bfa"/><circle cx="17" cy="19" r="1.1" fill="#e8ecf8"/><circle cx="29" cy="19" r="1.1" fill="#e8ecf8"/><path d="M16 27q6 4 12 0" stroke="#4ade80" stroke-width="2.2" stroke-linecap="round" fill="none"/><rect x="2.5" y="17" width="4" height="10" rx="2" fill="#8b5cf6"/><rect x="37.5" y="17" width="4" height="10" rx="2" fill="#8b5cf6"/></svg>'
        '<div style="font-weight:800;font-size:1.02rem;line-height:1.15">'
        'AI Resume<br>Analyzer</div></div>'
        '<div style="font-size:.76rem;color:#8b95b5;margin-bottom:.9rem">'
        'Smart AI to analyze your resume and get hired faster.</div>',
        unsafe_allow_html=True)

    st.session_state.page = st.radio(
        "Nav",
        ["Dashboard", "Resume Analysis", "Job Matching", "Reports",
         "AI Suggestions", "Interview Q&A", "Cover Letter", "Settings"],
        label_visibility="collapsed")

    st.divider()
    st.session_state.dark = st.toggle("🌙 Dark mode", value=st.session_state.dark)

    st.markdown(
        f'<div class="prof" style="margin-top:.9rem">'
        f'<div class="prof-av">AM</div><div>'
        f'<div class="prof-n">Ayesha Mumtaz</div>'
        f'<div style="font-size:.68rem;color:#8b95b5">Data Analyst</div>'
        f'</div></div>', unsafe_allow_html=True)

page = st.session_state.page
res = st.session_state.results


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
USER_NAME = "Ayesha Mumtaz"
USER_ROLE = "Data Analyst"
INITIALS = "".join(w[0] for w in USER_NAME.split()[:2]).upper()

h1, h2, h3 = st.columns([2.2, 1.5, 1.1])
with h1:
    st.markdown(
        f'<div style="font-size:1.28rem;font-weight:800;color:{TXT}">'
        f'Welcome back, {USER_NAME.split()[0]}! 👋</div>'
        f'<div style="font-size:.83rem;color:{MUTED}">Let\'s analyze your resume '
        f'and match the perfect job.</div>', unsafe_allow_html=True)
with h2:
    st.markdown(f'<div class="search">🔍 Search...</div>', unsafe_allow_html=True)
with h3:
    st.markdown(
        f'<div style="display:flex;gap:.5rem;align-items:center;justify-content:flex-end">'
        f'<span class="pill p-info">🔔 {len(st.session_state.history)}</span>'
        f'<div class="prof"><div class="prof-av">{INITIALS}</div><div>'
        f'<div class="prof-n">{USER_NAME}</div>'
        f'<div class="prof-p">{USER_ROLE}</div></div></div></div>',
        unsafe_allow_html=True)

with st.expander("Profile menu"):
    pc1, pc2, pc3, pc4 = st.columns(4)
    pc1.markdown(f'<div style="font-size:.82rem">👤 Profile</div>', unsafe_allow_html=True)
    pc2.markdown(f'<div style="font-size:.82rem">⚙️ Settings</div>', unsafe_allow_html=True)
    pc3.markdown(f'<div style="font-size:.82rem">🌙 Theme</div>', unsafe_allow_html=True)
    pc4.markdown(f'<div style="font-size:.82rem">↪ Logout</div>', unsafe_allow_html=True)

st.markdown('<div class="brand"><svg width="30" height="30" viewBox="0 0 44 44" fill="none" style="vertical-align:-6px;margin-right:8px"><line x1="22" y1="4" x2="22" y2="10" stroke="#a78bfa" stroke-width="2.4" stroke-linecap="round"/><circle cx="22" cy="4" r="2.8" fill="#4ade80"/><rect x="7" y="10" width="30" height="24" rx="8" fill="#8b5cf6" fill-opacity=".2" stroke="#a78bfa" stroke-width="2.4"/><circle cx="16" cy="20" r="3.3" fill="#a78bfa"/><circle cx="28" cy="20" r="3.3" fill="#a78bfa"/><circle cx="17" cy="19" r="1.2" fill="#e8ecf8"/><circle cx="29" cy="19" r="1.2" fill="#e8ecf8"/><path d="M16 27q6 4 12 0" stroke="#4ade80" stroke-width="2.4" stroke-linecap="round" fill="none"/><rect x="2.5" y="17" width="4" height="10" rx="2" fill="#8b5cf6"/><rect x="37.5" y="17" width="4" height="10" rx="2" fill="#8b5cf6"/></svg>AI RESUME ANALYZER</div>'
            '<div class="brand-sub">Get AI-powered insights to improve your '
            'resume and match the perfect job.</div>', unsafe_allow_html=True)


def metric_row(r) -> None:
    """Render the five top metric cards."""
    m = r or {}
    score = m.get("score", 0)
    ats = m.get("ats", 0)
    matched = len(m.get("matched", []))
    total = matched + len(m.get("missing", []))
    missing = len(m.get("missing", []))
    exp = m.get("exp", {"rating": 0, "label": "-"})
    pct = round(matched / total * 100) if total else 0

    c = st.columns(5)
    c[0].markdown(metric("Match Score", f"{score:.0f}%",
                         "Excellent Match" if score >= 75 else
                         "Good Match" if score >= 50 else "Needs Work",
                         "#4ade80" if score >= 50 else "#fb923c",
                         ring(score, "#a78bfa")), unsafe_allow_html=True)
    c[1].markdown(metric("ATS Score", f"{ats:.0f}%",
                         "Highly Optimized" if ats >= 75 else "Can Improve",
                         "#4ade80" if ats >= 75 else "#fb923c",
                         ring(ats, "#22c55e")), unsafe_allow_html=True)
    c[2].markdown(metric("Skills Matched",
                         f'{matched:02d} <span style="font-size:.9rem;color:#8b95b5">/ {total}</span>',
                         f"{pct}% Matched", "#60a5fa",
                         icon_box("👥", "#60a5fa")), unsafe_allow_html=True)
    c[3].markdown(metric("Missing Skills", f"{missing:02d}",
                         "Important to Add", "#fb923c",
                         icon_box("🔗", "#fb923c")), unsafe_allow_html=True)
    c[4].markdown(metric("Experience Match",
                         f'{exp["rating"]} <span style="font-size:.9rem;color:#8b95b5">/ 5</span>',
                         exp["label"], "#60a5fa",
                         icon_box("💼", "#60a5fa")), unsafe_allow_html=True)


def bottom_stats() -> None:
    s = st.session_state.stats
    hours = round(s["resumes"] * 0.75, 1)
    items = [("📁", "Resumes Analyzed", f'{s["resumes"]:02d}'),
             ("💼", "Jobs Matched", f'{s["jobs"]:02d}'),
             ("📄", "Reports Generated", f'{s["reports"]:02d}'),
             ("👤", "Interviews Prepped", f'{s["interviews"]:02d}'),
             ("⏱️", "Time Saved", f"{hours} hrs")]
    cells = "".join(
        f'<div style="display:flex;gap:.55rem;align-items:center">'
        f'<div class="icon-box" style="background:#8b5cf622;color:#a78bfa">{i}</div>'
        f'<div><div class="stat-v">{v}</div><div class="stat-l">{l}</div></div></div>'
        for i, l, v in items)
    st.markdown(
        f'<div class="statbar"><div style="display:flex;justify-content:space-between;'
        f'flex-wrap:wrap;gap:1rem;align-items:center">{cells}'
        f'<div style="font-size:.78rem;color:{MUTED};max-width:210px;text-align:right">'
        f'Keep improving! Your next opportunity is closer than you think. 🚀</div>'
        f'</div></div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# DASHBOARD
# --------------------------------------------------------------------------- #
if page == "Dashboard":
    metric_row(res)
    st.write("")

    up, jd, how = st.columns([1.05, 1.25, 0.85])

    with up:
        st.markdown('<div class="sec">Upload Your Resume</div>', unsafe_allow_html=True)
        resume_file = st.file_uploader("Drag & drop your PDF file here",
                                       type=["pdf"], label_visibility="collapsed")
        st.caption("PDF only • Max size 10MB")
        resume_manual = st.text_area("or paste resume text", height=78,
                                     placeholder="...or paste resume text here",
                                     label_visibility="collapsed")
        if resume_file:
            kb = round(len(resume_file.getvalue()) / 1024)
            st.markdown(
                f'<div class="card" style="display:flex;gap:.6rem;align-items:center">'
                f'<span style="font-size:1.1rem">📄</span><div style="flex:1">'
                f'<div style="font-size:.82rem;font-weight:600">{resume_file.name}</div>'
                f'<div style="font-size:.72rem;color:{MUTED}">{kb} KB</div></div>'
                f'<span style="color:#4ade80;font-size:1.1rem">✓</span></div>',
                unsafe_allow_html=True)

    with jd:
        st.markdown('<div class="sec">Job Description</div>', unsafe_allow_html=True)
        job_text = st.text_area(
            "Job description", height=222, max_chars=6000,
            placeholder="We are looking for a Data Analyst who can work with large "
                        "datasets, create reports, and generate insights...",
            label_visibility="collapsed")
        st.markdown(f'<div style="text-align:right;font-size:.72rem;color:{MUTED}">'
                    f'{len(job_text)} / 6000</div>', unsafe_allow_html=True)

    with how:
        st.markdown('<div class="sec">How it works</div>', unsafe_allow_html=True)
        steps = [("1", "Upload Resume", "Upload your CV in PDF format."),
                 ("2", "Paste Job Description", "Add the full job posting details."),
                 ("3", "Get AI Insights", "Match score, missing skills, suggestions.")]
        body = "".join(
            f'<div class="step"><div class="step-n">{n}</div><div>'
            f'<div class="step-t">{t}</div><div class="step-d">{d}</div></div></div>'
            for n, t, d in steps)
        st.markdown(f'<div class="card">{body}</div>', unsafe_allow_html=True)

    st.write("")
    if st.button("Analyze Resume  ✨"):
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

        stages = ["Uploading resume", "Extracting text", "Identifying skills",
                  "Matching with job description", "Generating AI suggestions"]
        prog, status = st.progress(0), st.empty()
        for i, sname in enumerate(stages, 1):
            status.markdown(f"**{sname}...**")
            prog.progress(int(i / len(stages) * 100))
            time.sleep(0.22)

        score = compute_similarity(resume_text, job_text)
        gap = compare_skills(resume_text, job_text)
        ats = compute_ats_score(resume_text, job_text)
        exp = experience_match(resume_text, job_text)
        prio = prioritise_missing(gap["missing"], job_text)
        partial = partial_matches(resume_text, job_text)
        tips = generate_suggestions(resume_text, job_text, score, gap)
        strength = overall_strength(score, ats["score"], exp["rating"])

        status.empty(); prog.empty()

        st.session_state.results = {
            "score": score, "ats": ats["score"], "checks": ats["checks"],
            "matched": gap["matched"], "missing": gap["missing"],
            "extra": gap["extra"], "partial": partial, "prio": prio,
            "exp": exp, "strength": strength, "tips": tips,
            "resume_text": resume_text, "job_text": job_text,
            "file_name": resume_file.name if resume_file else "pasted_text.txt",
        }
        day = (datetime.now()).strftime("%b %d")
        st.session_state.history.append((day, score))
        st.session_state.stats["resumes"] += 1
        st.session_state.stats["jobs"] += 1
        st.rerun()

    # ---- Results ----
    if res:
        st.write("")
        a, b, c = st.columns([1, 1, 1])

        with a:
            matched_n = len(res["matched"])
            missing_n = len(res["missing"])
            partial_n = len(res["partial"])
            total = matched_n + missing_n or 1
            pm = round(matched_n / total * 100)
            st.markdown(
                f'<div class="card"><div class="sec">Skills Match Overview</div>'
                f'<div style="display:flex;gap:1rem;align-items:center">'
                f'<div style="position:relative;text-align:center">'
                f'{ring(pm, "#22c55e", 118, 13)}'
                f'<div style="position:absolute;top:50%;left:50%;'
                f'transform:translate(-50%,-50%)">'
                f'<div style="font-size:.66rem;color:{MUTED}">Total</div>'
                f'<div style="font-size:1.35rem;font-weight:800">{total}</div>'
                f'</div></div><div style="font-size:.8rem;line-height:2">'
                f'<div><span class="dot" style="background:#4ade80"></span>'
                f'Matched Skills<br><span style="color:{MUTED};margin-left:12px">'
                f'{matched_n} ({pm}%)</span></div>'
                f'<div><span class="dot" style="background:#f87171"></span>'
                f'Missing Skills<br><span style="color:{MUTED};margin-left:12px">'
                f'{missing_n} ({100-pm}%)</span></div>'
                f'<div><span class="dot" style="background:#fb923c"></span>'
                f'Partial Match<br><span style="color:{MUTED};margin-left:12px">'
                f'{partial_n}</span></div></div></div></div>',
                unsafe_allow_html=True)

        with b:
            bars = ""
            for i, s in enumerate(res["matched"][:5]):
                bars += bar(s.title(), max(60, 95 - i * 5), "f-green")
            if not bars:
                bars = f'<div style="color:{MUTED};font-size:.82rem">No matches yet.</div>'
            st.markdown(f'<div class="card"><div class="sec">Top Matched Skills</div>'
                        f'{bars}</div>', unsafe_allow_html=True)

        with c:
            bars = ""
            for skill, level in res["prio"][:5]:
                cls = {"High": "badge-high", "Medium": "badge-med",
                       "Low": "badge-low"}[level]
                pct = {"High": 25, "Medium": 45, "Low": 60}[level]
                bars += bar(skill.title(), pct, "f-orange",
                            f'<span class="{cls}">{level}</span>')
            if not bars:
                bars = f'<div style="color:{MUTED};font-size:.82rem">Nothing missing 🎉</div>'
            st.markdown(f'<div class="card"><div class="sec">Missing Important Skills'
                        f'</div>{bars}</div>', unsafe_allow_html=True)

        st.write("")
        d, e, f = st.columns([1, 1, 1])

        with d:
            lines = [ln.strip("*-• ") for ln in res["tips"].split("\n")
                     if len(ln.strip()) > 30][:4]
            icons = ["💡", "🛡️", "✏️", "📊"]
            body = "".join(
                f'<div class="sug"><span class="sug-i">{icons[i % 4]}</span>'
                f'<span>{ln[:95]}</span><span class="chev">›</span></div>'
                for i, ln in enumerate(lines))
            st.markdown(f'<div class="card"><div class="sec">AI Suggestions</div>'
                        f'{body}</div>', unsafe_allow_html=True)

        with e:
            txt = res["resume_text"]
            per = 900
            pages = max(1, (len(txt) + per - 1) // per)
            pg = st.number_input("Page", 1, pages, 1, key="prev_pg",
                                 label_visibility="collapsed")
            chunk = txt[(pg - 1) * per: pg * per]
            st.markdown(
                f'<div class="card"><div class="sec">Resume Preview</div>'
                f'<div style="background:rgba(255,255,255,.03);border-radius:10px;'
                f'padding:.7rem;max-height:190px;overflow:auto">'
                f'<pre style="white-space:pre-wrap;font-size:.7rem;color:{MUTED};'
                f'margin:0;font-family:Inter">{chunk}</pre></div>'
                f'<div style="font-size:.7rem;color:{MUTED};margin-top:.4rem">'
                f'Page {pg} / {pages}</div></div>', unsafe_allow_html=True)

        with f:
            st.markdown(f'<div class="card"><div class="sec">Score History</div>'
                        f'{line_chart(st.session_state.history[-6:], TXT, MUTED)}'
                        f'</div>', unsafe_allow_html=True)

        st.write("")
        g, h = st.columns([1, 1])
        with g:
            tech = ["Python", "Streamlit", "PyPDF2", "spaCy", "scikit-learn", "Gemini API"]
            body = "".join(f'<div style="font-size:.82rem;margin:.28rem 0">'
                           f'<span style="color:#4ade80">✓</span> {t}</div>' for t in tech)
            st.markdown(f'<div class="card"><div class="sec" style="color:#a78bfa">'
                        f'Technologies used</div>{body}</div>', unsafe_allow_html=True)
        with h:
            sg = res["strength"]
            st.markdown(
                f'<div class="strength"><div style="display:flex;'
                f'justify-content:space-between;align-items:center">'
                f'<div><div style="font-weight:700;font-size:.95rem">Overall Strength'
                f'</div><div style="color:#a78bfa;font-weight:800;font-size:1.05rem;'
                f'margin:.15rem 0">{sg["label"]}</div>'
                f'<div style="font-size:.78rem;color:{MUTED};max-width:250px">'
                f'{sg["detail"]}</div></div>'
                f'<div style="font-size:2rem">🏆</div></div></div>',
                unsafe_allow_html=True)

    bottom_stats()


# --------------------------------------------------------------------------- #
# RESUME ANALYSIS
# --------------------------------------------------------------------------- #
elif page == "Resume Analysis":
    if not res:
        st.info("Run an analysis from **Dashboard** first.")
    else:
        metric_row(res)
        st.write("")
        st.markdown('<div class="sec">ATS Checks</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, chk in enumerate(res["checks"]):
            mark = "✓" if chk["passed"] else "✗"
            cls = "p-ok" if chk["passed"] else "p-no"
            cols[i % 3].markdown(
                f'<div class="card" style="margin-bottom:.7rem">'
                f'<span class="pill {cls}">{mark} {chk["label"]}</span>'
                f'<div style="font-size:.76rem;color:{MUTED};margin-top:.35rem">'
                f'{chk["detail"]}</div></div>', unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="sec">Skills by category</div>', unsafe_allow_html=True)
        by_cat: dict = {}
        for s in sorted(set(res["matched"] + res["missing"])):
            by_cat.setdefault(category_of(s), []).append(s)
        cats = sorted(by_cat.items())
        cols = st.columns(min(3, len(cats)) or 1)
        for i, (cat, items) in enumerate(cats):
            body = "".join(
                f'<span class="pill {"p-ok" if s in res["matched"] else "p-no"}">{s}</span>'
                for s in items)
            cols[i % len(cols)].markdown(
                f'<div class="card" style="margin-bottom:.7rem">'
                f'<div class="step-t">{cat}</div>{body}</div>', unsafe_allow_html=True)

        with st.expander("Full extracted text"):
            st.text(res["resume_text"][:5000])


# --------------------------------------------------------------------------- #
# JOB MATCHING
# --------------------------------------------------------------------------- #
elif page == "Job Matching":
    if not res:
        st.info("Run an analysis from **Dashboard** first.")
    else:
        metric_row(res)
        st.write("")
        a, b = st.columns(2)
        with a:
            pills = "".join(f'<span class="pill p-ok">✓ {s}</span>'
                            for s in res["matched"]) or "None"
            st.markdown(f'<div class="card"><div class="sec">Strengths</div>'
                        f'{pills}</div>', unsafe_allow_html=True)
        with b:
            pills = "".join(f'<span class="pill p-no">✗ {s}</span>'
                            for s in res["missing"]) or "Nothing missing"
            st.markdown(f'<div class="card"><div class="sec">Missing Skills</div>'
                        f'{pills}</div>', unsafe_allow_html=True)

        st.write("")
        exp = res["exp"]
        st.markdown(
            f'<div class="card"><div class="sec">Experience Match</div>'
            f'<div style="font-size:.85rem">Job asks for about '
            f'<b>{exp["required"]} years</b>; your resume suggests '
            f'<b>{exp["held"]} years</b>. Rating: <b>{exp["rating"]}/5</b> '
            f'({exp["label"]})</div></div>', unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="sec">Salary Estimate</div>', unsafe_allow_html=True)
        est = estimate_salary(res["job_text"], res["resume_text"])
        c = st.columns(3)
        for col, (lab, key, colour) in zip(
                c, [("Low", "low", "#60a5fa"), ("Typical", "mid", "#4ade80"),
                    ("High", "high", "#fb923c")]):
            col.markdown(metric(lab, f'{est[key]//1000}k PKR', "per month", colour,
                                icon_box("💰", colour)), unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(format_salary(est))


# --------------------------------------------------------------------------- #
# REPORTS
# --------------------------------------------------------------------------- #
elif page == "Reports":
    if not res:
        st.info("Run an analysis from **Dashboard** first.")
    else:
        metric_row(res)
        st.write("")
        report = f"""# AI Resume Analyzer - Report

## Scores
- Match score: {res['score']:.0f}%
- ATS score: {res['ats']:.0f}%
- Experience match: {res['exp']['rating']}/5 ({res['exp']['label']})
- Overall strength: {res['strength']['label']}

## Skills
- Matched ({len(res['matched'])}): {", ".join(res['matched']) or "none"}
- Missing ({len(res['missing'])}): {", ".join(res['missing']) or "none"}
- Partial: {", ".join(res['partial']) or "none"}

## Priority of missing skills
{chr(10).join(f"- {s} — {p}" for s, p in res['prio']) or "- none"}

## AI suggestions
{res['tips']}
"""
        st.markdown('<div class="sec">Analysis Results</div>', unsafe_allow_html=True)
        r1 = st.columns(4)
        for col, (lab, val, colour) in zip(r1, [
                ("Overall", f"{res['score']:.0f}%", "#a78bfa"),
                ("ATS Score", f"{res['ats']:.0f}%", "#4ade80"),
                ("Skills Found", f"{len(res['matched'])}", "#60a5fa"),
                ("Missing Skills", f"{len(res['missing']):02d}", "#fb923c")]):
            col.markdown(
                f'<div class="card click" style="text-align:center">'
                f'<div class="m-sub">{lab}</div>'
                f'<div style="font-size:1.5rem;font-weight:800;color:{colour}">'
                f'{val}</div></div>', unsafe_allow_html=True)

        st.write("")
        r2 = st.columns(3)
        with r2[0]:
            pills = "".join(f'<div style="font-size:.8rem;margin:.25rem 0">'
                            f'<span style="color:#4ade80">●</span> {s}</div>'
                            for s in res["matched"][:6]) or "None"
            st.markdown(f'<div class="card"><div class="step-t">Strengths</div>'
                        f'{pills}</div>', unsafe_allow_html=True)
        with r2[1]:
            pills = "".join(f'<div style="font-size:.8rem;margin:.25rem 0">'
                            f'<span style="color:#f87171">●</span> {s}</div>'
                            for s in res["missing"][:6]) or "None"
            st.markdown(f'<div class="card"><div class="step-t">Missing Skills</div>'
                        f'{pills}</div>', unsafe_allow_html=True)
        with r2[2]:
            st.markdown(
                f'<div class="card"><div class="step-t">Recommendations</div>'
                f'<div style="font-size:.78rem;color:{MUTED};margin-top:.35rem">'
                f'{res["strength"]["detail"]} Add more projects, certifications, '
                f'and improve your summary.</div></div>', unsafe_allow_html=True)

        st.write("")
        b1, b2 = st.columns(2)
        with b1:
            if st.download_button("⬇ Download Report", report,
                                  file_name="resume_report.md",
                                  use_container_width=True):
                st.session_state.stats["reports"] += 1
        with b2:
            if st.button("🔗 Share Report", use_container_width=True):
                st.info("Copy the report text below to share it.")
                st.code(report[:1200], language="markdown")

        with st.expander("Full report preview"):
            st.markdown(report)


# --------------------------------------------------------------------------- #
# AI SUGGESTIONS
# --------------------------------------------------------------------------- #
elif page == "AI Suggestions":
    if not res:
        st.info("Run an analysis from **Dashboard** first.")
    else:
        metric_row(res)
        st.write("")
        with st.container(border=True):
            st.markdown(res["tips"])

        st.write("")
        t1, t2 = st.tabs(["Resume Rewrite", "Learning Roadmap"])
        with t1:
            if st.button("Rewrite my bullets"):
                with st.spinner("Rewriting..."):
                    st.session_state.rw = rewrite_bullets(res["resume_text"],
                                                          res["job_text"])
            if st.session_state.get("rw"):
                with st.container(border=True):
                    st.markdown(st.session_state.rw)
        with t2:
            weeks = st.slider("Plan length (weeks)", 4, 16, 8)
            if st.button("Build my roadmap"):
                with st.spinner("Planning..."):
                    st.session_state.rm = build_roadmap(res["missing"], weeks)
            if st.session_state.get("rm"):
                with st.container(border=True):
                    st.markdown(st.session_state.rm)


# --------------------------------------------------------------------------- #
# INTERVIEW Q&A
# --------------------------------------------------------------------------- #
elif page == "Interview Q&A":
    if not res:
        st.info("Run an analysis from **Dashboard** first.")
    else:
        st.markdown('<div class="sec">Interview Q&A Generator</div>',
                    unsafe_allow_html=True)
        st.caption("Likely questions for this job, with hints on how to answer.")
        if st.button("Generate questions"):
            with st.spinner("Preparing..."):
                st.session_state.qa = generate_interview_qa(res["resume_text"],
                                                            res["job_text"])
                st.session_state.stats["interviews"] += 1
        if st.session_state.get("qa"):
            with st.container(border=True):
                st.markdown(st.session_state.qa)


# --------------------------------------------------------------------------- #
# COVER LETTER
# --------------------------------------------------------------------------- #
elif page == "Cover Letter":
    if not res:
        st.info("Run an analysis from **Dashboard** first.")
    else:
        st.markdown('<div class="sec">Cover Letter Generator</div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        name = c1.text_input("Your name", placeholder="Ayesha Mumtaz")
        company = c2.text_input("Company name", placeholder="DataCorp")
        if st.button("Generate cover letter"):
            with st.spinner("Writing..."):
                st.session_state.cl = generate_cover_letter(
                    res["resume_text"], res["job_text"], name, company)
        if st.session_state.get("cl"):
            with st.container(border=True):
                st.markdown(st.session_state.cl)
            st.download_button("⬇ Download letter (.md)", st.session_state.cl,
                               file_name="cover_letter.md")


# --------------------------------------------------------------------------- #
# SETTINGS
# --------------------------------------------------------------------------- #
else:
    st.markdown('<div class="sec">Settings</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card"><div class="step-t">AI suggestions</div>'
        f'<div style="font-size:.82rem;color:{MUTED};margin-top:.4rem">'
        f'The app works without any API key using rule-based advice. To enable '
        f'Gemini-written rewrites, letters and Q&amp;A, add a <code>GEMINI_API_KEY'
        f'</code> to your <code>.env</code> file locally, or to <b>Manage app → '
        f'Settings → Secrets</b> on Streamlit Cloud.</div></div>',
        unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    if c1.button("Clear current analysis"):
        st.session_state.results = None
        st.success("Cleared.")
    if c2.button("Reset score history"):
        st.session_state.history = []
        st.session_state.stats = {"resumes": 0, "jobs": 0, "reports": 0,
                                  "interviews": 0}
        st.success("History reset.")


# --------------------------------------------------------------------------- #
# FOOTER (moved out of the sidebar, per the design)
# --------------------------------------------------------------------------- #
st.markdown(
    f'<div class="foot">© 2026 Ayesha Mumtaz &nbsp;|&nbsp; Built with Python • '
    f'Streamlit • Gemini API &nbsp;|&nbsp; '
    f'<a href="https://github.com/ayeshamumtaz1057/ai-resume-analyzer" '
    f'target="_blank">GitHub</a> • '
    f'<a href="https://www.linkedin.com" target="_blank">LinkedIn</a></div>',
    unsafe_allow_html=True)
