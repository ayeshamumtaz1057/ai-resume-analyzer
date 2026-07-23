# AI Resume Analyzer

Upload a resume, paste a job description, get a match score with the reasoning shown — which skills are evidenced, which are missing, and what to fix.

Built with Python, Streamlit, spaCy, scikit-learn and the Google Gemini API.

---

## Why this exists

Most resume checkers return a single number with no explanation. This one shows its work: the score decomposes into three measurable parts, and every skill verdict is traceable to text in your resume.

## How the score is built

| Component | Weight | What it measures |
|---|---|---|
| Skill coverage | 55% | Of the skills the posting asks for, how many the resume actually evidences |
| Text similarity | 30% | TF-IDF cosine similarity between resume and posting (1–2 grams, sublinear tf) |
| Resume quality | 15% | Section completeness, quantified metrics, action verbs, length |

Three details that matter more than the weights:

**Skills are matched by token, not substring.** A spaCy `PhraseMatcher` handles this, so `R` never matches inside `React` and `Go` never matches inside `Google` — the failure mode that makes naive keyword checkers useless.

**Repetition signals depth.** Naming a skill once earns 70%; using it across three sections earns 100%. A skills-list keyword and a skill you actually shipped with should not score the same.

**Tools imply skills.** Listing PyTorch is real evidence of deep learning even if the phrase never appears. The `IMPLIES` map in `core/skills_db.py` grants partial credit for this, and the UI labels it `implied` — because keyword filters at the other end usually won't make that inference for you.

Core technical skills (Python, SQL, cloud, ML) are weighted double against soft skills when the posting asks for them.

## Running it

```bash
git clone https://github.com/<you>/ai-resume-analyzer.git
cd ai-resume-analyzer
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run app.py
```

Open http://localhost:8501.

### Gemini API key (optional)

```bash
cp .env.example .env   # then add your key from https://aistudio.google.com/apikey
```

Without a key the app still runs end to end — suggestions come from a rule engine that reads the same analysis object. The UI labels which one produced them. This is deliberate: a reviewer cloning the repo gets a working demo on the first try, and a quota error at runtime degrades instead of crashing.

## Running the tests

```bash
PYTHONPATH=. pytest -q
```

Eleven tests cover section parsing, substring-collision guards, implied-skill credit, and score calibration at both ends of the range. The calibration tests are the useful ones — they caught a scoring bug where a resume containing every required skill only scored 57%.

## Project layout

```
app.py                 Streamlit UI
core/
  parser.py            PDF text extraction, section splitting
  extractor.py         spaCy PhraseMatcher, regex fallback
  skills_db.py         ~60 skills with aliases + implication map
  scorer.py            TF-IDF similarity, coverage, quality heuristics
  suggestions.py       Gemini client with rule-based fallback
  report.py            PDF report generation (reportlab)
tests/test_core.py
```

## Engineering notes

- **Scanned PDFs fail loudly.** If extraction yields under 30 words the app says the file is probably an image export and tells you how to fix it, rather than scoring an empty string as 0%.
- **spaCy degrades twice.** Missing model falls back to a blank English pipeline; missing spaCy entirely falls back to word-boundary regex. The app never hard-crashes on a fresh environment.
- **The matcher is built once** and cached with `lru_cache` — compiling ~200 alias patterns on every keystroke would make the UI crawl.
- **Weights live in one dict** (`WEIGHTS` in `scorer.py`) so the scoring model can be tuned without touching logic.

## Limitations

Scores reflect keyword and structure signals, not hiring outcomes. The skill taxonomy is tech-focused and would need extending for other fields. TF-IDF has no semantic understanding — "led a team" and "managed engineers" read as unrelated; sentence embeddings would fix this and are the obvious next step.

## License

MIT
