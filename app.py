"""AI Resume Analyzer — Streamlit front end."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from core import history
from core.auth import AuthError, STORAGE_WARNING, change_password, sign_in, sign_up
from core.parser import ResumeParseError, parse_resume
from core.report import build_report
from core.scorer import Analysis, analyse
from core.suggestions import generate

load_dotenv()

# Streamlit Cloud has no .env — secrets live in st.secrets. Copy them into the
# environment so core/ stays framework-agnostic and testable outside Streamlit.
try:
    for _key in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GEMINI_MODEL"):
        if _key in st.secrets and not os.getenv(_key):
            os.environ[_key] = str(st.secrets[_key])
except Exception:
    pass  # No secrets.toml locally — .env or the rule engine covers it.

st.set_page_config(page_title="AI Resume Analyzer", page_icon="🤖", layout="wide")

CSS = """
<style>
  .stApp { background:#F4F7FC; }

  /* ---- sidebar ---- */
  section[data-testid="stSidebar"] { background:#0B1730; }
  section[data-testid="stSidebar"] * { color:#C7D2E4; }
  section[data-testid="stSidebar"] h1 { color:#fff; font-size:1.2rem; letter-spacing:-.02em; }
  section[data-testid="stSidebar"] div[role="radiogroup"] label {
      padding:9px 12px; border-radius:9px; margin-bottom:3px; font-weight:500; }
  section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background:#16243F; }

  /* ---- masthead ---- */
  .mast { text-align:center; padding:6px 0 20px; }
  .mast h1 { font-size:2.5rem; font-weight:800; letter-spacing:-.03em; margin:0;
             color:#0B1730; line-height:1.1; }
  .mast h1 span { color:#2563EB; }
  .mast p { color:#5B6B85; margin:6px 0 0; font-size:1rem; }

  /* ---- cards ---- */
  .card { background:#fff; border:1px solid #E4EAF3; border-radius:16px;
          padding:22px 24px; margin-bottom:16px; box-shadow:0 1px 2px rgba(16,32,64,.04); }
  .card h3 { margin:0 0 16px; font-size:.98rem; color:#1D4ED8; font-weight:700;
             letter-spacing:-.01em; }
  .card h3.warn { color:#DC2626; }

  /* ---- check / cross rows ---- */
  .ck { display:flex; align-items:center; gap:10px; margin-bottom:11px;
        font-size:.92rem; color:#1F2937; }
  .ck i { width:19px; height:19px; border-radius:50%; flex:none; font-style:normal;
          font-size:12px; line-height:19px; text-align:center; font-weight:700; }
  .ck i.y { background:#16A34A; color:#fff; }
  .ck i.n { background:#EF4444; color:#fff; }
  .ck em { font-style:normal; color:#94A3B8; font-size:.78rem; }

  /* ---- meters ---- */
  .meter { height:9px; background:#EDF1F7; border-radius:99px; overflow:hidden; }
  .meter > span { display:block; height:100%; border-radius:99px; }
  .row { display:flex; align-items:center; gap:12px; margin-bottom:11px;
         font-size:.88rem; color:#334155; }
  .row .lbl { width:145px; flex:none; }
  .row .val { width:46px; flex:none; text-align:right; font-weight:700; color:#0B1730; }
  .row .bar { flex:1; }

  /* ---- how it works ---- */
  .stp { display:flex; gap:13px; margin-bottom:15px; }
  .stp b { width:31px; height:31px; border-radius:50%; flex:none; color:#fff;
           font-size:.85rem; line-height:31px; text-align:center; }
  .stp div { font-size:.83rem; color:#5B6B85; line-height:1.45; }
  .stp div u { display:block; color:#0B1730; font-weight:700; text-decoration:none;
               font-size:.89rem; margin-bottom:1px; }

  /* ---- tech list ---- */
  .tech { background:#F0FDF4; border:1px solid #C9EED8; }
  .tech h3 { color:#15803D; }
  .tech .ck { font-size:.87rem; margin-bottom:8px; }

  /* ---- key features strip ---- */
  .feat { background:#fff; border:1px solid #E4EAF3; border-radius:16px;
          padding:20px 10px; margin-top:8px; display:flex; flex-wrap:wrap;
          justify-content:space-around; gap:14px; }
  .feat div { text-align:center; width:135px; }
  .feat span { display:block; width:44px; height:44px; border-radius:50%; margin:0 auto 9px;
               font-size:19px; line-height:44px; }
  .feat p { margin:0; font-size:.79rem; color:#475569; font-weight:600; line-height:1.3; }

  /* sidebar logo block */
  .logo { display:flex; align-items:center; gap:11px; padding:2px 0 4px; }
  .logo span { width:42px; height:42px; border-radius:11px; background:#fff; flex:none;
               font-size:22px; line-height:42px; text-align:center; }
  .logo b { color:#fff; font-size:1.05rem; line-height:1.25; font-weight:700; }
  .logo b i { color:#60A5FA; font-style:normal; }

  /* red logout button */
  section[data-testid="stSidebar"] .stButton button {
      background:transparent; border:1px solid #7F1D1D; color:#F87171; font-weight:600; }
  section[data-testid="stSidebar"] .stButton button:hover {
      background:#7F1D1D; color:#fff; border-color:#7F1D1D; }

  /* uploaded file confirmation card */
  .fileok { display:flex; align-items:center; gap:13px; border:1px solid #E4EAF3;
            border-radius:11px; padding:13px 15px; background:#FCFDFF; }
  .fileok .ic { width:37px; height:37px; border-radius:8px; background:#FEE2E2; flex:none;
                color:#DC2626; font-size:11px; font-weight:800; line-height:37px;
                text-align:center; }
  .fileok .nm { flex:1; font-size:.92rem; font-weight:600; color:#0B1730; }
  .fileok .nm small { display:block; font-weight:400; color:#94A3B8; font-size:.78rem; }
  .fileok .tick { color:#16A34A; font-size:19px; }

  .counter { text-align:right; font-size:.78rem; color:#94A3B8; margin-top:-8px; }

  header[data-testid="stHeader"] { background:transparent; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def donut(value: int, color: str) -> str:
    """SVG progress ring. 2*pi*r with r=54 gives the full circumference."""
    circumference = 339.29
    filled = circumference * value / 100
    return (
        f'<svg viewBox="0 0 130 130" width="168" height="168">'
        f'<circle cx="65" cy="65" r="54" fill="none" stroke="#EDF1F7" stroke-width="13"/>'
        f'<circle cx="65" cy="65" r="54" fill="none" stroke="{color}" stroke-width="13"'
        f' stroke-linecap="round" stroke-dasharray="{filled:.1f} {circumference}"'
        f' transform="rotate(-90 65 65)"/>'
        f'<text x="65" y="72" text-anchor="middle" font-size="30" font-weight="800"'
        f' fill="#0B1730" font-family="sans-serif">{value}%</text></svg>'
    )


def check(label: str, ok: bool, note: str = "") -> str:
    mark, cls = ("\u2713", "y") if ok else ("\u2715", "n")
    extra = f" <em>{note}</em>" if note else ""
    return f'<div class="ck"><i class="{cls}">{mark}</i>{label}{extra}</div>'


def bar(label: str, value: int, color: str) -> str:
    return (
        f'<div class="row"><span class="lbl">{label}</span>'
        f'<span class="bar"><span class="meter"><span style="width:{value}%;background:{color}"></span>'
        f"</span></span><span class=\"val\">{value}%</span></div>"
    )


def skill_color(v: int) -> str:
    return "#16A34A" if v >= 70 else "#F59E0B" if v >= 40 else "#EF4444"


# ---------------------------------------------------------------- sidebar
st.session_state.setdefault("user", None)

with st.sidebar:
    st.markdown(
        '<div class="logo"><span>\U0001F916</span>'
        "<b><i>AI</i> Resume<br>Analyzer</b></div>",
        unsafe_allow_html=True,
    )
    st.caption("Match your resume against any job description.")
    st.divider()

    user = st.session_state["user"]
    pages = ["\U0001F4CA Dashboard", "\U0001F4C8 Analysis detail", "\u2139\uFE0F How it works"]
    if user:
        pages.insert(2, "\U0001F551 History")
        pages.append("\U0001F464 Profile")
    choice = st.radio("Navigate", pages, label_visibility="collapsed")
    page = choice.split(" ", 1)[1]  # strip the icon before comparing

    st.divider()
    if user:
        st.markdown(f"Signed in as **{user.name}**")
        if st.button("Sign out", use_container_width=True):
            st.session_state["user"] = None
            st.rerun()
    else:
        st.caption("Signing in is optional — it saves your history so you can track score changes.")
        with st.expander("Sign in or create an account"):
            tab_in, tab_up = st.tabs(["Sign in", "Sign up"])
            with tab_in:
                e = st.text_input("Email", key="in_email")
                p = st.text_input("Password", type="password", key="in_pw")
                if st.button("Sign in", use_container_width=True, key="btn_in"):
                    try:
                        st.session_state["user"] = sign_in(e, p)
                        st.rerun()
                    except AuthError as exc:
                        st.error(str(exc))
            with tab_up:
                n = st.text_input("Name", key="up_name")
                e2 = st.text_input("Email", key="up_email")
                p1 = st.text_input("Password", type="password", key="up_pw")
                p2 = st.text_input("Confirm password", type="password", key="up_pw2")
                if st.button("Create account", use_container_width=True, key="btn_up"):
                    try:
                        st.session_state["user"] = sign_up(e2, n, p1, p2)
                        st.rerun()
                    except AuthError as exc:
                        st.error(str(exc))
            st.caption(STORAGE_WARNING)

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

if page == "History":
    user = st.session_state["user"]
    st.title("History")
    entries = history.list_for(user.email)
    if not entries:
        st.info("No saved analyses yet. Run one from the Dashboard.")
        st.stop()

    movement = history.trend(user.email)
    if movement:
        first, latest = movement
        st.metric("Latest score", f"{latest}%", f"{latest - first:+d}% since your first run")

    for e in entries:
        when = e["timestamp"].replace("T", " ")[:16]
        with st.expander(f"{e['overall']}% · {e['job_title']} · {when}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Skill coverage", f"{e['skill_coverage']}%")
            c2.metric("Similarity", f"{e['similarity']}%")
            c3.metric("Quality", f"{e['quality']}%")
            st.write("**Matched:** " + (", ".join(e["matched"]) or "none"))
            st.write("**Missing:** " + (", ".join(e["missing"]) or "none"))
            st.caption(f"Resume file: {e['filename']}")

    if st.button("Clear history"):
        history.clear(user.email)
        st.rerun()
    st.stop()

if page == "Profile":
    user = st.session_state["user"]
    st.title("Profile")
    st.write(f"**{user.name}**")
    st.write(user.email)
    st.caption(f"Account created {user.created_at.replace('T', ' ')[:16]}")
    st.caption(f"Saved analyses: {len(history.list_for(user.email))}")

    st.subheader("Change password")
    cur = st.text_input("Current password", type="password")
    new1 = st.text_input("New password", type="password")
    new2 = st.text_input("Confirm new password", type="password")
    if st.button("Update password"):
        try:
            change_password(user.email, cur, new1, new2)
            st.success("Password updated.")
        except AuthError as exc:
            st.error(str(exc))

    st.divider()
    st.caption(STORAGE_WARNING)
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
st.markdown(
    '<div class="mast"><h1>\U0001F916 <span>AI</span> RESUME ANALYZER</h1>'
    "<p>Get AI-powered feedback and improve your resume.</p></div>",
    unsafe_allow_html=True,
)

left, right = st.columns([3, 1], gap="large")

with left:
    up_col, jd_col = st.columns(2, gap="medium")

    with up_col:
        st.markdown(
            '<div class="card"><h3>1. Upload your resume (PDF)</h3>', unsafe_allow_html=True
        )
        upload = st.file_uploader("Resume", type=["pdf"], label_visibility="collapsed")
        if upload:
            size = len(upload.getvalue()) / 1024
            unit = f"{size:.0f} KB" if size < 1024 else f"{size / 1024:.1f} MB"
            st.markdown(
                f'<div class="fileok"><div class="ic">PDF</div>'
                f'<div class="nm">{upload.name}<small>{unit}</small></div>'
                f'<div class="tick">\u2714</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with jd_col:
        st.markdown(
            '<div class="card"><h3>2. Paste the job description</h3>', unsafe_allow_html=True
        )
        jd = st.text_area(
            "Job description", height=150, max_chars=6000, label_visibility="collapsed",
            placeholder="Paste the full posting here \u2014 responsibilities and requirements both.",
        )
        st.markdown(f'<div class="counter">{len(jd)}/6000</div>', unsafe_allow_html=True)
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
                if st.session_state["user"]:
                    history.add(st.session_state["user"].email, result, upload.name, jd)
            except ResumeParseError as exc:
                st.error(str(exc))

with right:
    steps = [
        ("#8B5CF6", "Upload resume", "Your CV in PDF format."),
        ("#2563EB", "Paste job description", "The full posting, requirements included."),
        ("#16A34A", "Get match score", "Skills, similarity and structure."),
        ("#F59E0B", "View suggestions", "Written from your actual text."),
        ("#7C3AED", "Download report", "A formatted PDF you can keep."),
    ]
    rows = "".join(
        f'<div class="stp"><b style="background:{c}">{i}</b>'
        f"<div><u>{title}</u>{body}</div></div>"
        for i, (c, title, body) in enumerate(steps, 1)
    )
    st.markdown(f'<div class="card"><h3>How it works</h3>{rows}</div>', unsafe_allow_html=True)

    tech = "".join(
        check(t, True)
        for t in ["Python", "Streamlit", "pypdf", "spaCy", "scikit-learn", "Gemini API"]
    )
    st.markdown(
        f'<div class="card tech"><h3>Technologies used</h3>{tech}</div>', unsafe_allow_html=True
    )

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
            check(s.name, True, "implied" if s.evidence == "implied" else "")
            for s in a.matched
        ) or "\u2014"
        note = (
            '<div style="color:#94A3B8;font-size:.78rem;margin-top:8px">'
            "&ldquo;implied&rdquo; means a tool you listed suggests this skill, but you never name it. "
            "Naming it directly scores higher with keyword filters.</div>"
            if any(s.evidence == "implied" for s in a.matched)
            else ""
        )
        st.markdown(f'<div class="card"><h3>Key strengths</h3>{pills}{note}</div>', unsafe_allow_html=True)

    with c3:
        pills = "".join(check(s.name, False) for s in a.missing) or "Full coverage \U0001F389"
        st.markdown(
            f'<div class="card"><h3 class="warn">Missing skills</h3>{pills}</div>',
            unsafe_allow_html=True,
        )

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
    src = st.session_state["source"]
    label = "Gemini" if src == "gemini" else f"rule engine — {src}"
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

FEATURES = [
    ("\U0001F4C4", "#EDE9FE", "PDF resume upload"),
    ("\U0001F9E0", "#DCFCE7", "Skill extraction"),
    ("\U0001F4CA", "#DBEAFE", "Match score"),
    ("\U0001F50D", "#FFEDD5", "Missing skill detection"),
    ("\U0001F4A1", "#FCE7F3", "Smart suggestions"),
    ("\u2B07\uFE0F", "#D1FAE5", "Download report"),
]
cells = "".join(
    f'<div><span style="background:{bg}">{icon}</span><p>{name}</p></div>'
    for icon, bg, name in FEATURES
)
st.markdown(f'<div class="feat">{cells}</div>', unsafe_allow_html=True)
