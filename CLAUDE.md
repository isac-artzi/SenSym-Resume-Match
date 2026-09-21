# SenSym Resume Match — project instructions for Claude Code

Read `PRD.md` before doing anything. It is the source of truth for scope, behavior, and UI. If the PRD and this file disagree, the PRD wins; if something is missing from both, choose the simplest option and note it in your summary.

## What this is

A free, open-source Streamlit app that tailors a student's resume to a job description and generates a cover letter, intro email, LinkedIn message, elevator pitch, interview prep, and gap analysis — all as DOCX. No database, nothing stored, student brings their own AI key. Runs locally (folders on disk) or on Streamlit Community Cloud (upload / ZIP download).

## Non-negotiables

- **Never invent or embellish.** Every claim in generated documents must trace to the student's source documents. The fidelity-check pass exists to enforce this; do not weaken it.
- **Store nothing.** No writes to disk on the server in cloud mode except a `tempfile` dir for ZIP assembly, deleted immediately after. API keys live only in `st.session_state`. No `st.cache_data` / `st.cache_resource` on user content. `gatherUsageStats = false`.
- **Keep it simple.** This repo is a teaching artifact students will read and extend. Modules under ~300 lines, functions over classes, no clever abstractions, no tests, no Docker, no CI. Prompts are plain-text files in `prompts/`, not Python strings.
- **No system binaries.** `pip install -r requirements.txt` must be the only setup step on macOS, Windows, and Linux. Images are read via the model's vision capability, not Tesseract.
- **Elegant UI.** Single page, light only, Notion-style: white, near-black text, one muted accent, generous whitespace, no emoji, Streamlit chrome hidden. All brand tokens in one place in `resume_match/ui.py`.

## Layout

```
app.py                  Streamlit entry point — layout only, no business logic
resume_match/config.py  load / validate / generate resume_match.env
resume_match/ingest.py  files, images, links → text with provenance
resume_match/llm.py     complete() and complete_json() over anthropic | openai | gemini | ollama
resume_match/pipeline.py profile → job analysis → bundle → fidelity check
resume_match/render.py  JSON bundle → DOCX files / ZIP
resume_match/ui.py      CSS, brand tokens, small UI helpers
prompts/                profile.txt, job_analysis.txt, bundle.txt, fidelity_check.txt
examples/               synthetic sample credentials and two sample job postings
```

## Conventions

- Python 3.11+. Type hints on public functions. Docstrings that a student can learn from — say *why*, not just what.
- Provider differences stay inside `llm.py`. Default model IDs are pinned in one dict there; check each provider's current docs for the right IDs before pinning.
- Ollama is reached through its OpenAI-compatible endpoint using the `openai` client with `base_url`.
- Errors surface as friendly `st.error` messages, never tracebacks. Malformed JSON from the model → one automatic retry, then a clear message.
- Commit small and often with clear messages. Never commit `resume_match.env` (it is in `.gitignore`); commit `resume_match.env.example` instead.
- Never use a real API key in examples, docs, or commits.

## GitHub public repo

https://github.com/isac-artzi/SenSym-Resume-Match

## Verifying your work

Run `streamlit run app.py` and exercise the full flow with the `examples/` folder. Check that: both sample jobs render all seven DOCX files and `application.json`; the DOCX files open cleanly (validate with `python-docx` round-trip); the fidelity check flags a deliberately planted unsupported claim when you test it; the config form downloads a valid `.env`; "Start over" clears session state including the key; the page looks calm and uncluttered at 1024 px.
