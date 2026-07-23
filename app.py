"""AI Resume Analyzer — Streamlit front end."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from core.parser import ResumeParseError, parse_resume
from core.report import build_report
from core.scorer import Analysis, analyse
from core.suggestions import generate

load_dotenv()

st.set_page_config(page_title="AI Resume Analyzer", page_icon="🤖", layout="wide")

CSS = """
<style>
  .stApp { background:#F6F8FC; }
  section[data-testid="stSidebar"] { background:#0B1730; }
  section[data-testid="stSidebar"] * { color:#CBD5E1; }
  section[data-testid="stSidebar"] h1 { color:#fff; font-size:1.25rem; }
  .card { background:#fff; border:1px solid #E6EBF3; border-radius:14px;
          padding:22px 24px; margin-bottom:16px; }
  .card h3 { margin:0 0 14px; font-size:1rem; color:#1E40AF; font-weight:700; }
  .score { font-size:3.4rem; font-weight:800; line-height:1; color:#0B1730; }
  .verdict { font-size:1.05rem; font-weight:700; margin-top:6px; }
  .pill { display:inline-block; padding:4px 11px; border-radius:999px;
          font-size:.8rem; margin:0 6px 6px 0; }
  .pill-ok { background:#E7F8EE; color:#15803D; }
  .pill-no { background:#FDECEC; color:#B91C1C; }
  .meter { height:9px; background:#EDF1F7; border-radius:99px; overflow:hidden; }
  .meter > span { display:block; height:100%; border-radius:99px; }
  .row { display:flex; align-items:center; gap:12px; margin-bottom:11px;
         font-size:.9rem; color:#334155; }
  .row .lbl { width:150px; flex:none; }
  .row .val { width:46px; flex:none; text-align:right; font-weight:600; color:#0B1730; }
  .row .bar { flex:1; }
  .step { font-size:.88rem; color:#475569; margin-bottom:12px; }
  .step b { color:#0B1730; display:block; }
  header[data-testid="stHeader"] { background:transparent; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def bar(label: str, value: int, color: str) -> str:
    return (
        f'<div class="row"><span class="lbl">{label}</span>'
        f'<span class="bar"><span class="meter"><span style="width:{value}%;background:{color}"></span>'
        f"</span></span><span class=\"val\">{value}%</span></div>"
    )


def skill_color(v: int) -> str:
    return "#16A34A" if v >= 70 else "#F59E0B" if v >= 40 else "#EF4444"


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("# 🤖 AI Resume Analyzer")
    st.caption("Match your resume against any job description.")
    st.divider()
    page = st.radio(
        "Navigate",
        ["Dashboard", "Analysis detail", "How it works"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Python · Streamlit · pypdf · spaCy · scikit-learn · Gemini")

# ---------------------------------------------------------------- state
st.session_state.setdefault("analysis", None)
st.session_state.setdefault("suggestions", [])
st.session_state.setdefault("source", "rules")
st.session_state.setdefault("filename", "")

# ---------------------------------------------------------------- pages
if page == "How it works":
    st.title("How it works")
    steps = [
        ("1. Upload your resume", "pypdf pulls the text out and splits it into sections by heading."),
        ("2. Paste the job description", "A spaCy PhraseMatcher finds every skill either document mentions."),
        ("3. Get a match score", "55% skill coverage, 30% TF-IDF cosine similarity, 15% resume quality."),
        ("4. Read the suggestions", "Gemini writes them from your actual text; a rule engine covers you offline."),
        ("5. Download the report", "A formatted PDF you can keep or share."),
    ]
    for title, body in steps:
        st.markdown(f'<div class="card"><b>{title}</b><br><span style="color:#475569">{body}</span></div>',
                    unsafe_allow_html=True)
    st.stop()

if page == "Analysis detail":
    a: Analysis | None = st.session_state["analysis"]
    if not a:
        st.info("Run an analysis on the Dashboard first.")
        st.stop()
    st.title("Analysis detail")
    c1, c2 = st.columns(2)
    c1.metric("Skill coverage", f"{a.skill_coverage}%")
    c1.metric("Resume quality", f"{a.quality}%")
    c2.metric("Text similarity", f"{a.similarity}%")
    c2.metric("Overall", f"{a.overall}%", a.verdict)
    st.subheader("Every skill found in the job description")
    st.dataframe(
        [{"Skill": s.name, "Evidence": s.evidence, "Strength": s.coverage}
         for s in a.matched + a.missing],
        use_container_width=True, hide_index=True,
    )
    st.subheader("Skills found in your resume")
    st.write(", ".join(a.resume_skills) or "None detected.")
    st.stop()

# ---------------------------------------------------------------- dashboard
st.title("AI Resume Analyzer")
st.caption("Get AI-powered feedback and improve your resume.")

left, right = st.columns([3, 1], gap="large")

with left:
    st.markdown('<div class="card"><h3>1. Upload your resume (PDF)</h3>', unsafe_allow_html=True)
    upload = st.file_uploader("Resume", type=["pdf"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>2. Paste the job description</h3>', unsafe_allow_html=True)
    jd = st.text_area("Job description", height=170, max_chars=6000, label_visibility="collapsed",
                      placeholder="Paste the full posting here — responsibilities and requirements both.")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Analyze resume", type="primary", use_container_width=True):
        if not upload:
            st.error("Upload a PDF resume to continue.")
        elif len(jd.split()) < 20:
            st.error("Paste a longer job description — at least 20 words — for a meaningful score.")
        else:
            try:
                with st.spinner("Reading your resume…"):
                    parsed = parse_resume(upload.getvalue())
                with st.spinner("Scoring the match…"):
                    result = analyse(parsed, jd)
                with st.spinner("Writing suggestions…"):
                    tips, source = generate(result, parsed.raw_text, jd)
                st.session_state.update(
                    analysis=result, suggestions=tips, source=source, filename=upload.name
                )
            except ResumeParseError as exc:
                st.error(str(exc))

with right:
    st.markdown('<div class="card"><h3>How it works</h3>', unsafe_allow_html=True)
    for line in [
        "<b>1. Upload resume</b>PDF format.",
        "<b>2. Paste job description</b>The full posting.",
        "<b>3. Get match score</b>Skills, similarity, quality.",
        "<b>4. View suggestions</b>Written from your text.",
        "<b>5. Download report</b>Formatted PDF.",
    ]:
        st.markdown(f'<div class="step">{line}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

a: Analysis | None = st.session_state["analysis"]
if a:
    st.divider()
    c1, c2, c3 = st.columns([1, 1.2, 1.2], gap="large")

    with c1:
        color = "#16A34A" if a.overall >= 65 else "#F59E0B" if a.overall >= 50 else "#EF4444"
        st.markdown(
            f'<div class="card"><h3>Overall match score</h3>'
            f'<div class="score" style="color:{color}">{a.overall}%</div>'
            f'<div class="verdict" style="color:{color}">{a.verdict}</div>'
            f'<div style="margin-top:14px">{bar("Skill coverage", a.skill_coverage, "#2563EB")}'
            f'{bar("Text similarity", a.similarity, "#7C3AED")}'
            f'{bar("Resume quality", a.quality, "#0EA5E9")}</div></div>',
            unsafe_allow_html=True,
        )

    with c2:
        pills = "".join(
            f'<span class="pill pill-ok">{s.name}'
            f'{" <i style=\'opacity:.65\'>implied</i>" if s.evidence == "implied" else ""}</span>'
            for s in a.matched
        ) or "—"
        note = (
            '<div style="color:#94A3B8;font-size:.78rem;margin-top:8px">'
            "&ldquo;implied&rdquo; means a tool you listed suggests this skill, but you never name it. "
            "Naming it directly scores higher with keyword filters.</div>"
            if any(s.evidence == "implied" for s in a.matched)
            else ""
        )
        st.markdown(f'<div class="card"><h3>Key strengths</h3>{pills}{note}</div>', unsafe_allow_html=True)

    with c3:
        pills = "".join(f'<span class="pill pill-no">{s.name}</span>' for s in a.missing) or "Full coverage 🎉"
        st.markdown(f'<div class="card"><h3>Missing skills</h3>{pills}</div>', unsafe_allow_html=True)

    d1, d2 = st.columns(2, gap="large")
    with d1:
        rows = "".join(
            bar(s.name, s.coverage, skill_color(s.coverage))
            for s in sorted(a.matched + a.missing, key=lambda x: -x.coverage)[:8]
        )
        st.markdown(f'<div class="card"><h3>Skills match</h3>{rows}</div>', unsafe_allow_html=True)
    with d2:
        rows = "".join(bar(k, v, "#2563EB") for k, v in a.section_scores.items())
        st.markdown(f'<div class="card"><h3>Resume sections score</h3>{rows}</div>', unsafe_allow_html=True)

    tips = st.session_state["suggestions"]
    bullets = "".join(f"<li style='margin-bottom:7px'>{t}</li>" for t in tips)
    label = "Gemini" if st.session_state["source"] == "gemini" else "rule engine"
    st.markdown(
        f'<div class="card"><h3>Suggestions for improvement '
        f'<span style="color:#94A3B8;font-weight:400">· {label}</span></h3>'
        f'<ul style="color:#334155;font-size:.93rem;padding-left:18px;margin:0">{bullets}</ul></div>',
        unsafe_allow_html=True,
    )

    st.download_button(
        "Download report as PDF",
        data=build_report(a, tips, st.session_state["filename"], st.session_state["source"]),
        file_name="resume-analysis-report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
