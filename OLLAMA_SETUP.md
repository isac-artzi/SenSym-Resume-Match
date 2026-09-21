# Running SenSym™ Resume Match with local models (Ollama)

This is the deep-dive version of the "Using Ollama" section in the main
[`README.md`](README.md): installing Ollama, picking a model that fits your
hardware, and pointing the app at it. Ollama only works in **local mode** —
if you're using the hosted Streamlit Community Cloud app, it can't reach a
model running on your own computer, so you'll need to run the app locally
(see the main README) to use any of this.

## Why use a local model at all

- **No API key, no per-use cost.** Everything runs on your own machine.
- **Nothing leaves your computer.** Your resume and the job posting never
  go to a third-party API.
- **Works offline**, once the model is downloaded.

The tradeoffs: it's slower than a hosted API, and smaller models that fit on
a laptop are less reliable at following instructions precisely — which
matters a lot for an app whose entire premise is "never invent anything."
See "What to expect," below.

## Hardware requirements

Rule of thumb: you need roughly as much free RAM as the model's download
size, plus some headroom for everything else running on your machine. Disk
space needed is about the same as the download size — models are cached
locally so you don't re-download them, but you can free the space back up
with `ollama rm <model>` when you're done with one.

| Model size | Minimum RAM | Comfortable | Notes |
|---|---|---|---|
| ~3B (e.g. a small Llama or Gemma variant) | 4–8 GB | 8 GB | Runs on almost any laptop from the last several years |
| ~7–8B (e.g. `llama3.1`) | 8 GB | 16 GB | Good default; what this app is configured to use out of the box |
| ~13–14B | 16 GB | 32 GB | Noticeably slower without a GPU |
| ~30–34B | 32 GB | 64 GB | A GPU is strongly recommended at this size |
| 70B+ | 48–64 GB+ | 64 GB+ or a real GPU | Not realistic on a typical student laptop |

**GPU acceleration is automatic and optional:**

- **Apple Silicon (M1/M2/M3/M4 Macs)** — used automatically via Metal, no
  setup needed.
- **NVIDIA GPUs (Windows/Linux)** — used automatically if you have a
  reasonably current NVIDIA driver installed.
- **AMD GPUs (Windows/Linux)** — used automatically with ROCm-compatible
  drivers.
- **No GPU** — Ollama still works, entirely on CPU. Expect generation to
  take noticeably longer (think minutes rather than seconds for a full
  bundle of seven documents), especially for larger models.

If you're not sure what fits your machine: start with a ~7–8B model. If it's
too slow, try a smaller one; if it's fast and you have RAM to spare, try
something larger.

## Installing Ollama

### macOS

**Option A — installer (easiest):**
1. Go to [ollama.com/download](https://ollama.com/download) and download
   Ollama for macOS (requires macOS 14 Sonoma or later).
2. Open the downloaded `.dmg` and drag Ollama into Applications.
3. Launch Ollama once from Applications. It adds a menu-bar icon and keeps
   running in the background from then on.

**Option B — command line:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows

**Option A — installer (easiest):**
1. Go to [ollama.com/download](https://ollama.com/download) and download
   the Windows installer (requires Windows 10 or later).
2. Run it. Ollama installs and starts running as a background service —
   look for its icon in the system tray.

**Option B — PowerShell:**
```powershell
irm https://ollama.com/install.ps1 | iex
```

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

This detects your distribution and sets Ollama up as a `systemd` service —
check it with `systemctl status ollama`. If you'd rather not run a script
from the internet (fair), manual install steps for your distro are at
[docs.ollama.com/linux](https://docs.ollama.com/linux).

## Verifying it's running

Ollama serves its API at `http://localhost:11434` once it's running, on all
three platforms:

```bash
curl http://localhost:11434
```

(PowerShell users: this `curl` command works as-is, or use
`Invoke-WebRequest http://localhost:11434`.) You should get back a short
"Ollama is running" message. If you get a connection error, Ollama isn't
running yet — check for the menu-bar/tray icon, or on Linux run
`ollama serve` in a terminal.

## Pulling a model

```bash
ollama pull llama3.1
```

This is the model SenSym Resume Match uses by default when you select the
Ollama provider (pinned in `resume_match/llm.py`) — a solid general-purpose
starting point that's comfortable on 16 GB of RAM.

Want something else? Browse current options at
[ollama.com/library](https://ollama.com/library) — this list moves fast, so
check there rather than assuming any specific model is still the newest.
Pull whichever one you want, then either set it as your default in
`resume_match/llm.py`, or just set `MODEL=<name>` in your `resume_match.env`
— the app will use whatever tag you point it at.

**Want image transcription (scanned diplomas or transcripts) to work with
Ollama?** You need a vision-capable model — look for one tagged "vision" in
the library. Without one, the app skips image files with a notice rather
than failing the whole run.

## Configuring SenSym Resume Match to use it

In the app's Setup section, or directly in `resume_match.env`:

```
LLM_PROVIDER=ollama
API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
MODEL=llama3.1          # or blank to use the app's built-in default
```

No API key is needed for Ollama — leave `API_KEY` blank.

## What to expect

Local models are meaningfully slower than a hosted API, and the smaller
sizes that actually fit on a laptop are more prone to instruction-following
mistakes than a large hosted model — which matters here specifically because
this app's entire premise is that it never invents anything about you. Read
the fidelity-check flags carefully when using a local model, more so than
you would with a hosted provider. If you're about to submit something for
real, a hosted provider's free or low-cost tier is worth considering even if
you're experimenting with Ollama otherwise.

## Troubleshooting

- **The app can't reach Ollama / connection refused** — make sure Ollama is
  actually running (menu-bar icon on macOS, tray icon on Windows,
  `systemctl status ollama` on Linux). If you changed the port, update
  `OLLAMA_BASE_URL` to match.
- **"model not found"** — you need to `ollama pull <model>` before the app
  can use it; the app doesn't pull models on your behalf.
- **Very slow generation** — expected without a GPU, or if the model is
  large relative to your RAM (your OS starts swapping to disk). Try a
  smaller model.
- **Image files get skipped with a notice** — your current model doesn't
  support vision. Pull a vision-capable model and point `MODEL=` at it.
- **Port 11434 is already in use** — something else on your machine is
  using it; find and stop that process, or configure Ollama to use a
  different port and update `OLLAMA_BASE_URL` to match.
