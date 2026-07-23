# 🧠 AI Resume Analyzer

Upload a resume, paste a job description, and instantly get a **match score**,
a **skill-gap analysis**, and **AI-powered improvement suggestions** — all
through a clean Streamlit interface.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B)
![License](https://img.shields.io/badge/License-MIT-green)

> **Live demo:** _add your Streamlit Cloud URL here after deploying_

---

## 📌 Project overview

AI Resume Analyzer helps job seekers tailor their resume to a specific job.
It extracts text from a PDF resume, compares it with a job description using
NLP, highlights which required skills are present or missing, and generates
practical suggestions to improve the resume.

## Features

- **Modern dashboard UI** - metric cards, donut charts, skill bars, dark mode
- **Sidebar navigation** - Home, Dashboard, Resume Analysis, Reports, Settings
- **PDF resume upload** and text extraction (PyPDF2)
- **Text preprocessing** with spaCy (tokenizing + stop-word removal)
- **Match score** using TF-IDF + cosine similarity (0-100%)
- **ATS score** - 6 automated checks (contact info, sections, keywords,
  measurable results, action verbs, length)
- **Skill detection** - strengths vs. missing skills across 8 categories
- **AI suggestions** via Google Gemini (rule-based fallback, works free)
- **AI Tools page** with six extra features:
  - AI Resume Rewrite (weak bullets to strong, quantified)
  - ATS Checker (6 automated checks with score ring)
  - Cover Letter Generator (downloadable)
  - Interview Q&A Generator (job-specific questions + hints)
  - Salary Estimator (seniority + role heuristics)
  - Learning Roadmap (week-by-week plan for missing skills)
- **Resume preview** with page navigation
- **Progress animation** during analysis
- **Downloadable report** (.md)
- **Responsive** layout
- **Tested** with pytest (25 tests)

## 🧰 Technologies used

| Purpose            | Tool                          |
|--------------------|-------------------------------|
| UI                 | Streamlit                     |
| PDF parsing        | PyPDF2                        |
| NLP preprocessing  | spaCy                         |
| Similarity scoring | scikit-learn (TF-IDF, cosine) |
| AI suggestions     | Google Gemini (optional)      |
| Config             | python-dotenv                 |
| Testing            | pytest                        |

## 🗂️ Folder structure

```
ai-resume-analyzer/
├── app.py                 # Streamlit UI
├── requirements.txt
├── README.md
├── DEPLOYMENT.md
├── .gitignore
├── .env.example           # copy to .env and add your Gemini key
├── .streamlit/config.toml # theme
├── utils/
│   ├── __init__.py
│   ├── pdf_reader.py       # PDF -> text (PyPDF2)
│   ├── preprocess.py       # cleaning + tokenizing (spaCy)
│   ├── similarity.py       # TF-IDF cosine similarity
│   ├── skills.py           # skills DB + detection + gap analysis
│   └── ai_helper.py        # Gemini suggestions + fallback
|   └── ats.py              # ATS friendliness scoring
├── data/
│   ├── sample_resume.pdf
│   └── sample_job.txt
├── assets/
│   ├── logo.png
│   └── screenshots/
└── tests/
    ├── __init__.py
    ├── test_preprocess.py
    ├── test_similarity.py
    └── test_skills.py
```

## ⚙️ Installation

```bash
# 1. Clone
git clone https://github.com/ayeshamumtaz1057/ai-resume-analyzer.git
cd ai-resume-analyzer

# 2. Virtual environment
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) enable Gemini AI suggestions
copy .env.example .env      # Windows  (macOS/Linux: cp .env.example .env)
# then open .env and paste your key from https://aistudio.google.com/apikey
```

> No spaCy model download is needed — the app uses spaCy's blank English
> pipeline and built-in stop words, so it runs immediately.

## ▶️ Usage

```bash
streamlit run app.py
```

1. Open http://localhost:8501
2. Upload `data/sample_resume.pdf` (or your own resume)
3. Paste the text from `data/sample_job.txt` (or a real job description)
4. Click **Analyze** to see the score, skill gap, and suggestions

## 🧪 Testing

```bash
pytest -q
```

## 📸 Screenshots

_Add screenshots to `assets/screenshots/` after running the app, then embed
them here:_

```
![Home](assets/screenshots/home.png)
![Results](assets/screenshots/results.png)
```

## 🚀 Deployment

Full step-by-step instructions are in [`DEPLOYMENT.md`](DEPLOYMENT.md).
Quick version: push to GitHub → deploy on
[Streamlit Community Cloud](https://share.streamlit.io) with main file `app.py`.

## 🔮 Future improvements

- Swap TF-IDF for semantic embeddings (sentence-transformers)
- Rank multiple resumes against one job
- Export a PDF report of the analysis
- Section-aware parsing (experience, education, projects)

## 📄 License

MIT — free to use, modify, and share.
