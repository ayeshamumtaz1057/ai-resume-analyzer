# 🚀 Deployment Guide — get a public link for LinkedIn

This guide takes you from local code to a live, shareable URL you can put on
your resume and LinkedIn. Recommended host: **Streamlit Community Cloud**
(free, no credit card, purpose‑built for Streamlit apps).

---

## Step 1 — Put the project on GitHub

```bash
cd ai-resume-analyzer

git init
git add .
git commit -m "AI Resume Analyzer: initial version"

# Create an EMPTY repo on github.com named 'ai-resume-analyzer', then:
git branch -M main
git remote add origin https://github.com/<your-username>/ai-resume-analyzer.git
git push -u origin main
```

> ⚠️ Never commit secrets. `.gitignore` already excludes `.env` and
> `.streamlit/secrets.toml`. Your API key must only live in the host's
> Secrets panel (Step 3), not in the code.

---

## Step 2 — Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **Create app → Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `<your-username>/ai-resume-analyzer`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Deploy**. First build takes 1–3 minutes.
5. You'll get a public URL like
   `https://ai-resume-analyzer-<hash>.streamlit.app`.

That link is what you share on LinkedIn.

---

## Step 3 — (Optional) enable Gemini‑powered suggestions

The app works without any key (rule‑based advice). To turn on richer AI
feedback:

1. In your deployed app → **⋮ menu → Settings → Secrets**.
2. Add:
   ```toml
   GEMINI_API_KEY = "your-gemini-key-here"
   ```
3. Save. The app restarts automatically and now calls Gemini.

Get a key at https://aistudio.google.com/apikey. (Usage is pay‑as‑you‑go; a demo
costs a few cents. If you'd rather keep it free, just skip this step — the
fallback still gives useful advice.)

---

## Step 4 — Polish for the portfolio

- **Add screenshots:** run the app, capture the landing + results views, save
  them in `assets/screenshots/`, and reference them in `README.md`.
- **Add the live URL** to the top of `README.md` (replace the placeholder).
- **Pin the repo** on your GitHub profile.

---

## Alternative hosts

| Host                       | Free tier | Notes                                    |
|----------------------------|-----------|------------------------------------------|
| Streamlit Community Cloud  | ✅        | Easiest for Streamlit; recommended.      |
| Hugging Face Spaces        | ✅        | Choose the **Streamlit** SDK when creating the Space. |
| Render                     | ✅*       | Use start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |

\*Render's free web services sleep when idle.

---

## 📢 LinkedIn post template

> 🚀 Just built & deployed an **AI Resume Analyzer**!
>
> It takes a resume + a job description and instantly returns a match score,
> a skill‑gap breakdown (what you have vs. what's missing), and concrete tips
> to improve — with an optional Gemini‑powered advice mode.
>
> 🛠️ Tech: Python, Streamlit, scikit‑learn (TF‑IDF + cosine similarity),
> pdfplumber, and the Anthropic API. Fully tested with pytest.
>
> 🔗 Live demo: <your-streamlit-url>
> 💻 Code: <your-github-url>
>
> Feedback welcome! #Python #MachineLearning #NLP #Streamlit #OpenToWork

**Tips for the post:** attach a screenshot or a short screen‑recording (posts
with media get far more reach), tag relevant skills, and reply to early
comments quickly to boost visibility.
