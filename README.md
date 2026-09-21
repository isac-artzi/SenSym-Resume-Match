# SenSym™ Resume Match

A free, open-source Streamlit app that turns your resume, transcripts, and a
job posting into a complete, honest application bundle: a tailored resume,
cover letter, introduction email, LinkedIn message, elevator pitch,
interview-prep notes, and a gap analysis — all as DOCX files you can open and
edit in Word.

This app is provided free of charge by **SenSym™** ([sensym.ai](https://sensym.ai))
as a tool for students and early-career job seekers. There's no catch and no
paywall in the app itself — you only ever pay your own AI provider directly
for the model calls the app makes on your behalf (see "Getting an API key"
below); SenSym never charges for the app and never sees your API key or your
documents.

**The guiding rule for every generated word: present you in the best honest
light. Never invent, never embellish.** Everything the app writes about you
has to trace back to something in your own documents; a dedicated fidelity
check flags anything that doesn't.

The app stores nothing — no database, no accounts, no logging of your
documents. You bring your own AI key (Anthropic, OpenAI, Gemini, or a local
Ollama model) and pay your own model costs, typically a few cents per job.

## Runs locally or on Streamlit Community Cloud — your choice

This is the same app, the same repo, and the same code either way. Run it
on your own computer for full control (folders on disk, local Ollama
models, nothing ever leaves your machine except calls to your chosen AI
provider), or use the hosted version on Streamlit Community Cloud for
zero-setup access from any browser, no `git clone` or Python install
required. Switch between them freely — a config file downloaded from one
works in the other.

| | Local | Cloud |
|---|---|---|
| Setup | `git clone`, `pip install`, `streamlit run app.py` | Open the hosted Streamlit Community Cloud URL — nothing to install |
| Your files | Point the app at folders on your computer | Drag-and-drop upload (or a `.zip`) |
| Output | Written to a folder on your computer | Downloaded as a `.zip`, plus individual file downloads |
| Local models (Ollama) | Supported | Not reachable from the cloud |

The app detects which mode you're in automatically — if the folders you
configured actually exist on the machine running the app, it's local mode;
otherwise it shows you the upload controls. You never have to choose; just
open the app the way you want to run it.

**Hosted app:** [sensym-resume-match-qpqhdbnvu93cut9trqbvyd.streamlit.app](https://sensym-resume-match-qpqhdbnvu93cut9trqbvyd.streamlit.app/) — open it and start using it right away, no setup required.

## Quick start (local)

Works the same way on macOS, Windows, and Linux — Python and a browser are
the only requirements. Pick your platform below. (If you'd rather skip the
virtual environment step, you can — it just keeps this app's dependencies
separate from anything else on your system, which is worth doing.)

<details>
<summary><strong>macOS</strong></summary>

Needs Python 3.11+. Check with `python3 --version`; if you don't have it,
install it from [python.org](https://www.python.org/downloads/macos/) or via
Homebrew (`brew install python@3.12`).

```bash
git clone https://github.com/isac-artzi/SenSym-Resume-Match.git
cd SenSym-Resume-Match
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

</details>

<details>
<summary><strong>Windows</strong></summary>

Needs Python 3.11+. Install it from
[python.org](https://www.python.org/downloads/windows/) — check "Add
python.exe to PATH" during install — or from the Microsoft Store. Check with
`python --version` in PowerShell.

```powershell
git clone https://github.com/isac-artzi/SenSym-Resume-Match.git
cd SenSym-Resume-Match
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks the activation script with an "execution policy"
error, run this once first (for the current session only, nothing
permanent): `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
Using Command Prompt instead of PowerShell? Activate with
`.venv\Scripts\activate.bat` instead of the `.ps1` line above.

</details>

<details>
<summary><strong>Linux</strong></summary>

Needs Python 3.11+ and the matching `venv` package. Most distributions ship
Python 3, but you may need the venv module separately, e.g. on
Debian/Ubuntu: `sudo apt install python3-venv`.

```bash
git clone https://github.com/isac-artzi/SenSym-Resume-Match.git
cd SenSym-Resume-Match
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

</details>

Whichever platform you're on, `streamlit run app.py` opens the app in your
default browser at `http://localhost:8501`. Leave the terminal window open
while you use the app; closing it stops the app. Next time, you don't need
to recreate the virtual environment — just `cd` into the folder, re-activate
it (the `source .venv/bin/activate` or `.venv\Scripts\Activate.ps1` line
above), and run `streamlit run app.py` again.

Then, in the app:

1. **Setup** — pick a provider and paste your API key (see "Getting an API
   key" below), or upload a `resume_match.env` file if you have one saved
   from before.
2. **Your materials** — point the app at a folder containing your resume,
   transcripts, and anything else worth including (see "What goes in your
   credentials folder").
3. **Jobs** — point the app at a folder of saved job postings.
4. **Generate** — tick the jobs you want; a rough cost estimate appears
   above the button (skip this if you're on Ollama — local models have no
   per-token cost). Click "Create application materials."
5. **Review** — read through each document, check any fidelity flags, and
   download.

Want to try it before gathering your own documents? Point `CREDENTIALS_DIR`
at `examples/credentials` and `JOBS_DIR` at `examples/jobs` — that's exactly
what the demo build uses. Download a starter config from the Setup form, or
copy `resume_match.env.example` to `resume_match.env` and edit it by hand.

## Quick start (cloud)

No install, no clone, no terminal — just a browser.

1. Open the hosted app URL (see "Hosted app" above).
2. **Setup** — pick a provider and paste your API key, or upload a
   `resume_match.env` file if you have one saved from before.
3. **Your materials** — drag in your resume, transcripts, and anything else
   worth including, or a `.zip` of them, instead of typing a folder path. Or
   paste a public Google Drive folder link ("Anyone with the link can view")
   and click "Fetch from Drive" — upload is the more reliable path, so treat
   Drive as a convenience and fall back to upload if a fetch fails.
4. **Jobs** — drag in your saved job postings the same way (upload, `.zip`,
   or a Drive folder link).
5. **Generate** — before you click, a rough cost estimate appears based on
   your documents and provider's pricing. It's an estimate, not a bill —
   your provider's own usage dashboard is the source of truth.
6. **Review** — tick the jobs you want, generate, check any fidelity flags,
   and download — either file by file or as one `.zip` of everything.

Nothing you upload touches the server's disk beyond a temporary file used to
assemble your ZIP download (or fetch a Drive folder), deleted immediately
after — see "Privacy" below.

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

Ollama installs on macOS, Windows, and Linux and lets you run the app
entirely on your own machine, with no API key and no per-use cost — you
trade that for slower generation and, on smaller models, a higher chance of
instruction-following mistakes.

1. Install Ollama from [ollama.com](https://ollama.com) (installers for all
   three platforms).
2. Pull a model: `ollama pull llama3.1` (or any model you prefer — a
   vision-capable model if you want scanned-image transcription to work).
3. In Setup, choose provider "ollama." No API key is needed.
4. Ollama only works in **local mode** — Streamlit Community Cloud can't
   reach a model running on your own machine.

**For installation steps per operating system, hardware requirements (how
much RAM/disk a given model needs), GPU notes, and troubleshooting, see
[`OLLAMA_SETUP.md`](OLLAMA_SETUP.md).**

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
[`EXTENDING.md`](EXTENDING.md) if you want to build on it. The code is
open source under MIT; "SenSym" and the SenSym™ name and branding are
trademarks of SenSym LLC and aren't covered by the code license — fork and
extend the app freely, just don't reuse the SenSym name/branding for a
different or competing product.
