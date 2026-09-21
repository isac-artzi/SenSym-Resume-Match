# SenSym Resume Match — Product Requirements Document

**Version:** 1.0 (v1 scope)
**Date:** September 20, 2026
**Owner:** Isac Artzi, SenSym LLC
**Status:** Approved for build — demo in class September 21, 2026

---

## 1. Summary

SenSym Resume Match is a free, open-source Streamlit app that takes a student's credentials (resume, transcripts, diplomas, project pages, personal sites) and one or more job descriptions, and produces a complete, honest application bundle for each job: a tailored resume, a cover letter, an introduction email, a LinkedIn message, a 30-second elevator pitch, interview-prep notes, and a gap analysis that tells the student what to study and do to become a stronger candidate.

The app stores nothing. It has no database, no accounts, and no logging of user content. Students bring their own AI key (Anthropic by default; OpenAI, Gemini, and local Ollama also supported) and pay their own model costs. It runs two ways: locally from a cloned GitHub repo, reading and writing ordinary folders on the student's computer, or on Streamlit Community Cloud, where the student uploads files and downloads a ZIP.

The guiding rule for every generated word: **present the student in the best honest light — never invent, never embellish.**

## 2. Goals and non-goals

### Goals

1. Let any student go from "here are my documents and a job posting" to "here is a submission-ready DOCX bundle" in a few minutes, with no setup beyond a config file.
2. Produce output that is truthful to the source documents, and make the gap between the student and the job visible and actionable.
3. Be simple enough that a student can read the whole codebase in an evening and extend it (the repo is a teaching artifact as much as a tool).
4. Store nothing, track nothing, and say so plainly in the UI.
5. Look and feel elegant: a calm, single-page, Notion-style interface with SenSym branding.

### Non-goals (v1)

- Job search, job scraping, or application tracking.
- Automated submission to LinkedIn, Workday, or any job board.
- User accounts, saved history, or team/instructor dashboards.
- Career-services workflows or institutional integrations.
- Preserving the student's original resume template (v1 renders a clean, ATS-friendly template of its own).
- Tests, CI, Docker. Keep it simple; students may add these later.

## 3. Users

The primary user is any student or early-career job seeker. GCU students are the first audience because that is where the app is demonstrated, but nothing in the app is GCU-specific. A secondary user is the student-developer who clones the repo to learn from it or extend it.

Assumptions about the primary user: comfortable saving files into folders and pasting an API key; not necessarily comfortable editing code or config files by hand (hence the in-app config form); may have a modest budget for API calls and needs to see cost expectations up front.

## 4. Two run modes

| | Local mode | Cloud mode |
|---|---|---|
| How it runs | `git clone` the public repo, `pip install -r requirements.txt`, `streamlit run app.py` | Open the public Streamlit Community Cloud URL |
| Credentials input | A folder on disk (path in config) | Drag-and-drop files or a ZIP; optional public Google Drive folder link |
| Jobs input | A folder on disk (path in config) | Drag-and-drop files or a ZIP; optional public Google Drive folder link |
| Output | Written to the output folder on disk, one subfolder per job, overwritten on re-run | Downloaded as a ZIP containing the same folder structure; individual DOCX downloads also offered |
| Config | `resume_match.env` at repo root is auto-loaded if present; otherwise upload or fill the form | Upload `resume_match.env` or fill the form; held in session memory only |
| Local LLM (Ollama) | Supported | Not reachable from the cloud (documented) |

The app detects its mode automatically: if the configured folder paths exist on the machine running the app, it is in local mode; otherwise it shows the upload controls. The student never has to choose.

Google Drive support in cloud mode is an optional convenience: the student pastes a link to a folder shared as "Anyone with the link can view," and the app fetches the files with `gdown`. Because public-folder fetching can be brittle, the UI presents upload as the primary path and Drive as a secondary "or fetch from a public Drive folder" option. If Drive fetching fails, the app explains and points to upload. This feature may be cut from the September 21 demo build (see §13).

## 5. Inputs

### 5.1 Credentials folder

Any mix of the following, in any number:

| Type | Extensions | How it is read |
|---|---|---|
| Resume(s) | .pdf, .docx, .txt, .md | Text extraction (`pypdf`, `python-docx`) |
| Transcripts, diplomas, certificates | .pdf, .docx, .txt, .md | Text extraction |
| Scanned diplomas / images | .png, .jpg, .jpeg, .webp | Sent to the chosen model's vision capability for transcription (no local OCR dependency). Ollama users need a vision-capable model or the file is skipped with a notice. |
| Web pages (portfolio, GitHub, personal site) | A `links.txt` file, one URL per line | Fetched with `requests` and stripped to text. LinkedIn and many dynamic sites block fetching, so the README tells students to save such pages as PDF ("Print → Save as PDF") and drop the file in the folder instead. |
| Optional preferences | `preferences.txt` or `preferences.md` | Free-text notes on tone, length, target role, things to avoid. Used if present, ignored if absent. |

The base resume is identified by filename (contains "resume" or "cv"). If several match, the UI offers a dropdown to choose one; the others are still read as supporting evidence.

### 5.2 Jobs folder

One file per job posting: .pdf, .docx, .txt, or .md. The README and the in-app empty state both explain why files, not URLs: postings on LinkedIn, Workday, Greenhouse, and similar sit behind logins or dynamic pages that cannot be fetched reliably, and a saved file gives the student a permanent record of exactly what they applied to. Instructions cover "Print → Save as PDF" and copy-paste into a .txt file. The company and role are inferred from the posting text (with the filename as fallback) and used to name the output folder.

### 5.3 Config file (`resume_match.env`)

Simple `.env` style, one `KEY=value` per line. The app offers a form that generates and downloads this file so students never have to hand-edit it; they can re-upload it in later sessions. Uploaded config is read into session memory and never written to disk on the server.

```
# --- AI provider ---
LLM_PROVIDER=anthropic          # anthropic | openai | gemini | ollama
API_KEY=sk-ant-...              # leave blank for ollama
MODEL=                          # optional; provider default used if blank
OLLAMA_BASE_URL=http://localhost:11434   # ollama only

# --- Folders (local mode) ---
CREDENTIALS_DIR=/Users/me/job-search/credentials
JOBS_DIR=/Users/me/job-search/jobs
OUTPUT_DIR=/Users/me/job-search/applications

# --- Folders (cloud mode, optional) ---
DRIVE_CREDENTIALS_URL=
DRIVE_JOBS_URL=

# --- Student preferences (all optional) ---
STUDENT_NAME=
TARGET_ROLE=
TONE=                           # e.g. "confident but understated"
RESUME_MAX_PAGES=1
AVOID=                          # e.g. "buzzwords, the word synergy"
```

Provider defaults: Anthropic → the current Claude Sonnet model; OpenAI → the current GPT-4-class default; Gemini → the current Flash or Pro default; Ollama → `llama3.1` (or whatever the student names). Exact model IDs are pinned in one place in code (`llm.py`) so they are easy to update. Ollama is reached through its OpenAI-compatible endpoint, so no extra dependency is needed; the README covers installing Ollama, pulling a model, and pointing the config at it.

## 6. Processing pipeline

Everything below runs in memory, per session, with progress shown in the UI. Prompts live as plain-text files in `prompts/` so students can read and modify them without touching code.

**Step 1 — Ingest.** Every file in the credentials folder (or upload) is converted to text. Images go through the model's vision capability. Links are fetched. Each source keeps its filename as a provenance tag.

**Step 2 — Build the credential profile (one model call, reused across all jobs).** The model extracts a structured JSON profile: contact details, education (with GPA and coursework if present), experience, projects, skills, certifications, publications, and an "evidence" field per item pointing to the source file. This is the only ground truth the later steps may draw on.

**Step 3 — Analyze the job (one call per job).** Extract company, role, seniority, must-have and nice-to-have requirements, keywords, and tone cues.

**Step 4 — Generate the bundle (one structured call per job, returning JSON).** Using only the credential profile and the job analysis, the model produces:

1. **Tailored resume** — the student's real experience reordered, reworded, and emphasized for this role; keywords from the posting used only where the student's evidence supports them.
2. **Cover letter** — one page, specific to the company and role.
3. **Introduction email** — short, to a recruiter or hiring manager, with a subject line.
4. **LinkedIn message** — under 300 characters, for a connection request or InMail.
5. **Elevator pitch** — 30 seconds spoken, roughly 75 words.
6. **Interview prep** — likely questions for this role, suggested talking points tied to the student's actual experience, and questions the student could ask.
7. **Gap analysis** — requirements the student meets, partially meets, and does not meet; for each gap, concrete suggestions: what to study (with the kind of resource — a course, a certification, a textbook topic), what to build or do (a project, a contribution, a volunteer role, a competition), and roughly how long it would take. Also a candid one-paragraph match summary.

**Step 5 — Fidelity check (one call per job).** A second pass compares every factual claim in the resume and cover letter against the credential profile and lists anything unsupported. Unsupported claims are shown to the student as flagged items in the review panel; the student can regenerate that document or edit after download. The app never silently ships an unsupported claim.

**Step 6 — Render.** Each document is rendered to DOCX with `python-docx` using a clean, ATS-friendly template (single column, standard headings, no tables or text boxes, system fonts). A machine-readable `application.json` holding the full structured bundle is written alongside, so students can re-render, diff, or build on it.

Model calls per job: roughly three, plus one shared profile call. A five-job batch is about sixteen calls. The UI shows an approximate cost estimate before generation, based on token counts and the provider's published pricing, with a clear "this is an estimate" label.

## 7. Outputs

One subfolder per job, named `<company>-<role>` (slugified), overwritten on re-run:

```
applications/
└── acme-data-scientist/
    ├── resume.docx
    ├── cover_letter.docx
    ├── intro_email.docx
    ├── linkedin_message.docx
    ├── elevator_pitch.docx
    ├── interview_prep.docx
    ├── gap_analysis.docx
    └── application.json
```

All end products are DOCX so students can edit before submitting. In cloud mode the same tree is delivered as `applications.zip`, plus per-document download buttons in the review panel.

## 8. User interface

A single page, top to bottom, that reads like a well-designed form rather than a dashboard. Notion-style: white background, near-black text, one muted accent color, generous whitespace, no sidebars, no cards-within-cards, no emoji. Light theme only. Streamlit's default chrome (menu, footer, "Deploy" button) is hidden; a small amount of custom CSS handles typography and spacing.

**Header.** SenSym wordmark, app name, one-line description, and the privacy line: "Nothing you upload is stored or tracked. Everything lives in your browser session and disappears when you close it."

**Section 1 — Setup.** Two tabs: *Upload a config file* or *Fill in the form*. The form has provider (radio), API key (password field), and the optional preferences; folder paths appear only in local mode. A "Download config" button saves `resume_match.env` for next time. Model and temperature sit in an *Advanced* expander, closed by default.

**Section 2 — Your materials.** In local mode: the credentials folder path with a list of detected files and their types, and a resume selector if more than one is found. In cloud mode: a drag-and-drop uploader (multiple files or ZIP) and the optional Drive link. A quiet status line confirms what was read ("7 files, 2 links · resume: Isac_Artzi_Resume.pdf").

**Section 3 — Jobs.** A checklist of the postings found, each with the inferred company and role once analyzed. A "Select all" toggle covers the batch case; ticking one job is the single-application case. The empty state explains how to save a posting as a file and why.

**Section 4 — Generate.** One primary button: "Create application materials." A progress indicator shows per-job stages (reading, analyzing, writing, checking, rendering). Cost estimate shown beside the button.

**Section 5 — Review.** One tab per job; within each, tabs per document. Each document shows a clean text preview, any fidelity flags, a "Regenerate this document" button, and a download button. The gap analysis tab shows a three-column met / partial / gap layout with the suggestions beneath. At the bottom: "Download everything (.zip)" in cloud mode, or "Saved to /path/applications" in local mode, with a "Start over" button that clears the session.

Keyboard and screen-reader basics apply: real labels on every control, sufficient contrast, no information conveyed by color alone.

Branding tokens (accent color, wordmark SVG, font) are defined once in `ui.py` so they can be swapped. SenSym brand colors and logo file to be supplied by Isac before the demo; a neutral placeholder is used until then.

## 9. Privacy and data handling

- No database, no file system writes on the server in cloud mode (temp files for ZIP assembly are created in a `tempfile` directory and deleted immediately after the ZIP is built).
- API keys live in `st.session_state` only, are never logged, and are cleared on "Start over" or session end.
- No `st.cache_data` or `st.cache_resource` on any user content.
- `.streamlit/config.toml` sets `gatherUsageStats = false`.
- No analytics, no third-party scripts.
- The only network calls are to the student's chosen model provider (and, if used, the student's own Drive link and the URLs the student listed).
- The README and the in-app privacy line state this in plain language. The README also advises students to create a dedicated API key with a spending limit and to rotate it after use, since they are pasting it into a public web app.
- Note for the README: the app itself stores nothing, but the model provider processes the text the student sends; students should read their provider's data policy.

## 10. Technical design

**Stack.** Python 3.11+, Streamlit, python-docx, pypdf, python-dotenv, requests, beautifulsoup4, anthropic, openai (also used for Ollama via its OpenAI-compatible API), google-genai, gdown (optional).

**Repository layout.**

```
sensym-resume-match/
├── app.py                    # Streamlit entry point; layout only
├── resume_match/
│   ├── config.py             # load/validate/generate resume_match.env
│   ├── ingest.py             # files, images, links → text with provenance
│   ├── llm.py                # one thin client over the four providers
│   ├── pipeline.py           # profile → job analysis → bundle → fidelity check
│   ├── render.py             # JSON bundle → DOCX files / ZIP
│   └── ui.py                 # CSS, brand tokens, small UI helpers
├── prompts/
│   ├── profile.txt
│   ├── job_analysis.txt
│   ├── bundle.txt
│   └── fidelity_check.txt
├── examples/                 # synthetic sample credentials + two sample jobs
├── .streamlit/config.toml    # theme, usage stats off
├── resume_match.env.example
├── requirements.txt
├── README.md                 # setup for both modes, Ollama, saving job postings, privacy
├── EXTENDING.md              # ideas and starting points for students
├── PRD.md                    # this document
└── LICENSE                   # MIT
```

**Design principles for the code.** Every module is under a few hundred lines. No classes where a function will do. The LLM client exposes exactly two functions: `complete(prompt, images=None) -> str` and `complete_json(prompt, schema_hint) -> dict`. Provider differences are confined to `llm.py`. Prompts are data, not code. Errors surface as friendly messages in the UI (bad key, rate limit, unreadable file, model returned malformed JSON → one automatic retry, then a clear message).

**Streamlit Cloud constraints.** Community Cloud gives roughly 1 GB RAM; the app processes one job at a time and discards intermediate text after rendering. Upload limit is set to 200 MB total. Long batches show progress so the session is not mistaken for a hang.

## 11. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| F1 | Read PDF, DOCX, TXT, MD from the credentials folder or upload | Must |
| F2 | Transcribe PNG/JPG/WEBP via the model's vision capability | Must |
| F3 | Fetch URLs listed in `links.txt`; fail gracefully per link | Must |
| F4 | Read job postings as PDF, DOCX, TXT, MD | Must |
| F5 | Auto-detect local vs cloud mode from config paths | Must |
| F6 | Upload or form-generate `resume_match.env`; download it; never persist it server-side | Must |
| F7 | Support Anthropic (default), OpenAI, Gemini, Ollama | Must |
| F8 | Job checklist supporting one or many selections | Must |
| F9 | Generate all seven documents per job from the credential profile only | Must |
| F10 | Fidelity check flags unsupported claims in the review panel | Must |
| F11 | Render all documents as DOCX; write `application.json` | Must |
| F12 | Local mode writes `<output>/<company>-<role>/`, overwriting; cloud mode offers ZIP and per-file downloads | Must |
| F13 | In-app preview, per-document regenerate, start-over | Must |
| F14 | Optional preferences (tone, target role, length, avoid) applied when present | Must |
| F15 | Cost estimate before generation | Should |
| F16 | Public Google Drive folder link as input in cloud mode | Could (v1.1) |
| F17 | Privacy line in UI; privacy section and key-hygiene advice in README | Must |
| F18 | README instructions for Ollama and for saving job postings as files | Must |
| F19 | EXTENDING.md with ideas for student contributors | Must |

## 12. Non-functional requirements

Generation for one job should complete in under about ninety seconds on a hosted model; a five-job batch in under seven minutes. The app must run on macOS, Windows, and Linux with only `pip install`. No step may require a system binary beyond Python (this is why images use model vision rather than Tesseract). The interface must be usable at 1024 px width and above. All user-facing text is in plain English at a level a first-year undergraduate can follow.

## 13. Delivery plan

**Demo build (September 21).** Local mode end to end with Anthropic; cloud mode with upload and ZIP download; all seven documents; fidelity check; config form; README and EXTENDING.md; `examples/` folder with synthetic data so the demo runs without real student documents. Drive link, cost estimate, and Gemini/OpenAI/Ollama can be stubbed behind the provider switch if time runs short, but the switch and README text should be present.

**v1.0 (following week).** Fill any stubs, deploy to Streamlit Community Cloud, share the repo link with students.

**v1.1 and beyond.** Driven by student contributions; see EXTENDING.md.

**Demo script.** Open the app, show the privacy line, upload (or auto-load) the config, point to the `examples/` credentials and two sample jobs, tick both jobs, generate, walk through the resume and gap analysis for one job, show a fidelity flag if one appears, download the ZIP, open a DOCX in Word. Then open the repo and show `prompts/bundle.txt` and `EXTENDING.md`. Ten minutes.

## 14. EXTENDING.md — seed ideas for students

The file will present these as invitations, each with a pointer to the module it touches and a rough difficulty. Deliberately ambitious, cross-disciplinary options are included alongside easy ones.

- A "resume A/B" mode that generates two tailored resumes with different emphases and lets the student compare.
- A skills-graph view: plot the student's skills against the job's requirements as a network or radar and animate the gap closing as the student adds planned activities.
- A "study plan compiler" that turns the gap analysis into a dated, week-by-week plan and exports it to a calendar file.
- Mock-interview mode: a voice or chat loop that asks the interview-prep questions and scores answers against the student's own evidence.
- Multilingual output for international applications, with a back-translation fidelity check.
- Portfolio site generator: render the credential profile as a static personal website.
- A local-only mode that runs entirely on Ollama with a small model, with prompt engineering to make small models hold the no-invention rule.
- A "recruiter's eye" critique agent that reads the finished resume the way a screener would in seven seconds and reports what it noticed.
- Accessibility pass: screen-reader-first layout, dyslexia-friendly typography option for generated DOCX.
- Fine-grained evidence links: every bullet in the generated resume carries a footnote to the exact source line it came from.
- Batch evaluation harness: a set of synthetic student profiles and postings, with an automatic hallucination scorer, so prompt changes can be measured rather than eyeballed.
- Integration experiments: pull job postings from an RSS feed or an ATS API, or push the bundle to a Google Drive folder the student owns.

## 15. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Model invents or inflates a claim | Profile-only grounding, explicit prompt rules, fidelity check pass, flags visible before download, editable DOCX |
| Student pastes an API key into a public app | Session-only handling, HTTPS, README guidance on limited-spend keys and rotation |
| Public Drive fetching breaks | Upload is primary; Drive is optional and fails with a clear message |
| LinkedIn/portfolio URLs cannot be fetched | Per-link graceful failure; README says to save as PDF |
| Large scanned transcripts blow up cost | Cost estimate shown; images sent at reduced resolution; per-file size cap with a notice |
| Streamlit Cloud memory limits on big batches | One job at a time, discard intermediates, upload cap |
| Model returns malformed JSON | Schema hint in prompt, one automatic retry, friendly error |
| Students expect the app to remember them | Privacy line and "download your config" make the stateless design a feature, not a surprise |

## 16. Open items

1. SenSym brand color(s), wordmark SVG, and preferred font — needed to replace the neutral placeholder before the demo.
2. Confirm the exact default model IDs to pin for each provider at build time.
3. Decide whether the demo build ships the Drive link feature or defers it to v1.1.
4. Repo name: `sensym-resume-match` is proposed.

## Appendix A — Decisions captured from the PRD Questions document (September 20, 2026)

Any student is a user; GCU is simply the first audience; no career-services involvement. Both single-job and batch runs are supported via a checklist. All listed file types are valid; students are told to save job postings (and blocked web pages) as files, with the reason explained. No invention or embellishment; the app points out gaps and suggests what to study and do. Voice and preference notes are optional and used when present. All end products are DOCX. Intro email, LinkedIn message, elevator pitch, and interview prep are all in scope. One subfolder per job, overwritten on re-run. Cloud mode uses upload/ZIP by default with public Drive as an optional convenience. Config is simple `.env` style, generated by an in-app form and downloadable for later re-upload. Anthropic is the default provider; OpenAI, Gemini, and Ollama are supported, with Ollama instructions in the README. Students supply their own key and bear all cost. The UI reassures students that nothing is stored or tracked. SenSym branding, light theme only, Notion style. Single-page flow with preview, download, and regenerate; editing happens after download. MIT license, no Docker, no tests, as simple as possible; demo in class the next day; repo shared with students together with a Markdown file of ideas for extending the app. No fixed date beyond the demo; standalone, not tied to any course or the book.
