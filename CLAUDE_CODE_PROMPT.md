# Kickoff prompt for Claude Code

Paste everything below the line into Claude Code in VS Code, from inside the `SenSym-resume-match` folder.

---

Build the SenSym Resume Match app described in `PRD.md`. Read `PRD.md` and `CLAUDE.md` fully before writing any code — they are the spec and the house rules, and I will not repeat them here.

**Scope for this session: the demo build in PRD §13.** I am demonstrating this in class tomorrow, so working and elegant beats complete. In priority order:

1. Repo scaffold: `git init`, MIT `LICENSE`, `.gitignore` (include `resume_match.env`, `applications/`, `__pycache__`, `.venv`), `requirements.txt`, `.streamlit/config.toml` with usage stats off and a light theme, `resume_match.env.example`.
2. `resume_match/llm.py` with `complete()` and `complete_json()` for Anthropic (default), OpenAI, Gemini, and Ollama. Implement Anthropic fully and test it; the other three must be wired and selectable but may be lightly tested. Look up current default model IDs from each provider's docs and pin them in one dict.
3. `resume_match/ingest.py`: PDF, DOCX, TXT, MD, images (via model vision), and `links.txt` fetching, each source tagged with its filename. Graceful per-file failure.
4. `prompts/` (four plain-text prompt files) and `resume_match/pipeline.py`: credential profile → job analysis → seven-document bundle as JSON → fidelity check. The no-invention rule must be explicit and prominent in every prompt.
5. `resume_match/render.py`: JSON bundle → seven clean, ATS-friendly DOCX files plus `application.json`, into `<output>/<company>-<role>/` (overwrite), or a ZIP in cloud mode.
6. `resume_match/config.py` and `app.py` + `resume_match/ui.py`: the single-page flow from PRD §8 — Setup (upload config or form, download config), Materials (auto-detected local folders or upload), Jobs checklist, Generate with progress, Review with per-job / per-document tabs, fidelity flags, regenerate, download, start over. Mode auto-detection per PRD §4.
7. `examples/`: a synthetic student (resume, transcript, a short `links.txt` pointing at a public page that fetches reliably, `preferences.txt`) and two sample job postings as `.txt`. Fictional names and companies only.
8. `README.md` (both run modes, Ollama setup, how and why to save job postings as files, privacy statement, API-key hygiene) and `EXTENDING.md` (expand the seed ideas in PRD §14 into invitations with the module each touches and a rough difficulty).

**GitHub public repor:** https://github.com/isac-artzi/SenSym-Resume-Match 

**Defer to v1.1 unless you finish early:** Google Drive link input, cost estimate. Leave a clear `# TODO(v1.1)` where each would go.

**How to work.** Plan briefly, then build in the order above, committing after each numbered step. Run the app with the `examples/` folder as you go and fix what you see; do not wait until the end to run it. Use my Anthropic key from the environment variable `ANTHROPIC_API_KEY` for testing — never write it into any file. If a design decision is not covered by the PRD, make the simpler choice and list it in your final summary rather than stopping to ask; only ask me if you are blocked. Use a neutral accent color and a text wordmark for SenSym for now; I will supply brand assets later.

**Definition of done for tonight.** From a fresh clone: `pip install -r requirements.txt`, `streamlit run app.py`, point the config at `examples/`, tick both jobs, generate, and get two folders of seven DOCX files plus `application.json` that open in Word and contain nothing the sample student did not actually do. The page should look like something a designer made, not a default Streamlit app.

When finished, give me: the commit log, the list of decisions you made beyond the PRD, anything deferred, and the exact commands to run the demo.
