# SenSym Resume Match

A free, open-source Streamlit app that turns your resume, transcripts, and a
job posting into a complete, honest application bundle: a tailored resume,
cover letter, introduction email, LinkedIn message, elevator pitch,
interview-prep notes, and a gap analysis — all as DOCX files you can open and
edit in Word.

**The guiding rule for every generated word: present you in the best honest
light. Never invent, never embellish.** Everything the app writes about you
has to trace back to something in your own documents; a dedicated fidelity
check flags anything that doesn't.

The app stores nothing — no database, no accounts, no logging of your
documents. You bring your own AI key (Anthropic, OpenAI, Gemini, or a local
Ollama model) and pay your own model costs, typically a few cents per job.

## Two ways to run it

| | Local | Cloud |
|---|---|---|
| Setup | `git clone`, `pip install`, `streamlit run app.py` | Open the hosted Streamlit Community Cloud URL |
| Your files | Point the app at folders on your computer | Drag-and-drop upload (or a `.zip`) |
| Output | Written to a folder on your computer | Downloaded as a `.zip`, plus individual file downloads |

The app detects which mode you're in automatically — if the folders you
configured actually exist on the machine running the app, it's local mode;
otherwise it shows you the upload controls.

## Quick start (local)

```bash
git clone https://github.com/isac-artzi/SenSym-Resume-Match.git
cd SenSym-Resume-Match
pip install -r requirements.txt
streamlit run app.py
```

Then, in the app:

1. **Setup** — pick a provider and paste your API key (see "Getting an API
   key" below), or upload a `resume_match.env` file if you have one saved
   from before.
2. **Your materials** — point the app at a folder containing your resume,
   transcripts, and anything else worth including (see "What goes in your
   credentials folder").
3. **Jobs** — point the app at a folder of saved job postings.
4. **Generate** — tick the jobs you want, and click "Create application
   materials."
5. **Review** — read through each document, check any fidelity flags, and
   download.

Want to try it before gathering your own documents? Point `CREDENTIALS_DIR`
at `examples/credentials` and `JOBS_DIR` at `examples/jobs` — that's exactly
what the demo build uses. Download a starter config from the Setup form, or
copy `resume_match.env.example` to `resume_match.env` and edit it by hand.

## Quick start (cloud)

Open the hosted app URL, fill in the Setup form (or upload a config file),
then drag your files into the Materials and Jobs uploaders instead of typing
folder paths. Everything else is the same.

## Getting an API key

The app defaults to **Anthropic** (Claude). Get a key at
[console.anthropic.com](https://console.anthropic.com). OpenAI, Gemini, and a
local [Ollama](https://ollama.com) install are also supported — pick your
provider in Setup.

**Because you're pasting a key into a web app (especially the hosted cloud
version), create a dedicated key with a spending limit if your provider
supports one, and rotate it (delete the old one, make a new one) once you're
done using the app for the day.** The app never writes your key to disk and
holds it only in your browser session, but a key that leaves your machine at
all is safer treated as temporary.

### Using Ollama (local models, no API key)

1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull a model: `ollama pull llama3.1` (or any model you prefer — a
   vision-capable model if you want scanned-image transcription to work).
3. In Setup, choose provider "ollama." No API key is needed.
4. Ollama only works in **local mode** — Streamlit Community Cloud can't
   reach a model running on your own machine.

## What goes in your credentials folder

Any mix of, in any number:

- **Resume(s)** — `.pdf`, `.docx`, `.txt`, `.md`. If you have more than one,
  the app looks for "resume" or "cv" in the filename and lets you pick the
  base one; the rest are still read as supporting evidence.
- **Transcripts, diplomas, certificates** — same file types.
- **Scanned images** — `.png`, `.jpg`, `.jpeg`, `.webp`. These are sent to
  your model's vision capability for transcription; no OCR software needed.
  (If you're on Ollama, this only works with a vision-capable model.)
- **`links.txt`** — one URL per line, for a portfolio, GitHub profile, or
  personal site. See "Why job postings and some links need to be files"
  below for why not every URL will fetch.
- **`preferences.txt`** or **`preferences.md`** — optional free-text notes:
  tone, target role, things to avoid. Used if present, ignored if absent.

## Why job postings need to be saved as files

Postings on LinkedIn, Workday, Greenhouse, and similar sites usually sit
behind a login or a page that only renders with JavaScript, so the app can't
reliably fetch them by URL. Instead:

1. Open the posting in your browser.
2. **Print → Save as PDF** (or select the text and paste it into a `.txt`
   file).
3. Save it into your jobs folder — one file per posting.

This also gives you a permanent record of exactly what you applied to, which
is worth having anyway.

The same logic applies to `links.txt`: if a link in there is LinkedIn or
another page that blocks fetching, save that page as a PDF too and drop it in
your credentials folder instead. The app tells you, per link, if a fetch
failed.

## Privacy

- **Nothing is stored.** No database, no server-side writes in cloud mode
  (temporary files used only to assemble your ZIP download are deleted
  immediately after). Local mode writes only to the output folder you
  configured, on your own computer.
- Your API key lives in the browser session only — never logged, never
  written to disk by the app, cleared when you click "Start over" or close
  the tab.
- No analytics, no third-party scripts, no usage tracking
  (`gatherUsageStats = false`).
- The only network calls the app makes are to the AI provider you chose, and
  to the URLs you explicitly listed in `links.txt` or a Drive link.
- The app itself stores nothing, but **your chosen model provider processes
  the text you send it.** Read your provider's data-handling policy if
  that matters for your situation — this varies by provider and by whether
  you're on a free or paid tier.

## Configuration reference

Copy `resume_match.env.example` to `resume_match.env` and edit it, or use the
in-app form (Setup → Fill in the form → Download config). A `resume_match.env`
placed at the repo root is loaded automatically the next time you run the
app locally.

```
LLM_PROVIDER=anthropic          # anthropic | openai | gemini | ollama
API_KEY=                        # leave blank for ollama
MODEL=                          # optional; provider default used if blank
OLLAMA_BASE_URL=http://localhost:11434

CREDENTIALS_DIR=/path/to/credentials
JOBS_DIR=/path/to/jobs
OUTPUT_DIR=/path/to/applications

STUDENT_NAME=
TARGET_ROLE=
TONE=
RESUME_MAX_PAGES=1
AVOID=
```

`resume_match.env` is in `.gitignore` — never commit your real config or your
key.

## What you get

One subfolder per job (local mode) or one entry per job in the downloaded
`.zip` (cloud mode), named `<company>-<role>`:

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
    └── application.json      # the full structured bundle, for re-rendering or building on
```

Every DOCX opens cleanly in Word (or any compatible editor) and is meant to
be edited before you submit it — the app gets you to a strong draft, not a
finished, un-reviewable artifact.

## Troubleshooting

- **"An API key is required"** — pick a provider other than Ollama and paste
  a key, or switch to Ollama.
- **A file didn't get read** — check the status line under "Your materials"
  or "Jobs"; unreadable files are skipped individually with a message rather
  than failing the whole run.
- **A link didn't fetch** — save that page as a PDF instead (see above).
- **The model returned something that couldn't be parsed** — the app retries
  automatically once; if it still fails, try again or switch models in the
  Advanced section of Setup.

## License

MIT — see `LICENSE`. This is a teaching artifact as much as a tool; see
[`EXTENDING.md`](EXTENDING.md) if you want to build on it.
