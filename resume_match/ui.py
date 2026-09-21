"""Brand tokens, CSS, and small UI helpers.

Everything visual lives here so a real SenSym logo/color can replace the
neutral placeholder later by editing this one file.
"""

from __future__ import annotations

import streamlit as st

ACCENT_COLOR = "#C1662E"  # warm terracotta
ACCENT_SOFT = "#F3DCC2"  # soft tint, for hover/highlight backgrounds
ACCENT_DARK = "#A24F1F"  # hover/active state for accent-colored buttons
TEXT_COLOR = "#2B2420"  # warm near-black
MUTED_TEXT_COLOR = "#8A7566"  # warm muted brown-gray
BACKGROUND_COLOR = "#FFFCF8"  # warm off-white
SURFACE_COLOR = "#F8F1E7"  # warm sand
BORDER_COLOR = "#EADFD0"  # warm taupe

APP_NAME = "SenSym Resume Match"
APP_TAGLINE = "Turn your credentials and a job posting into a submission-ready application bundle."
PRIVACY_LINE = (
    "Nothing you upload is stored or tracked. Everything lives in your browser "
    "session and disappears when you close it."
)

SENSYM_URL = "https://sensym.ai"
WORDMARK_TEXT = "SenSym™"  # TODO: replace with the real SVG wordmark once brand assets arrive
FREE_APP_LINE = f'A free app from SenSym™ — <a href="{SENSYM_URL}" target="_blank" rel="noopener">sensym.ai</a>'

# Tooltip copy for widgets across app.py, kept in one place alongside the
# other UI text so the layout script stays focused on wiring, not prose.
TOOLTIPS = {
    "config_upload": "Upload a config file you downloaded from this app before — it fills in "
    "your provider, key, and preferences automatically for this session.",
    "provider": "Which AI service writes your documents. Anthropic is the default; Ollama runs "
    "a model on your own computer, needs no key, and only works in local mode.",
    "api_key": "From your provider's website (e.g. console.anthropic.com for Anthropic). Held "
    "only in this browser session — never written to disk by the app, never sent anywhere "
    "except your provider.",
    "ollama_url": "The address Ollama is listening on. The default is correct unless you "
    "changed Ollama's port.",
    "CREDENTIALS_DIR": "A folder on this computer with your resume, transcripts, and anything "
    "else worth including — see 'What goes in your credentials folder' in the README.",
    "JOBS_DIR": "A folder on this computer with one file per job posting you're applying to.",
    "OUTPUT_DIR": "Where finished application bundles are saved, one subfolder per job. "
    "Running again overwrites that job's folder.",
    "STUDENT_NAME": "Used to personalize documents, e.g. the cover letter greeting.",
    "TARGET_ROLE": "A role or title to keep the tailoring focused on, if it isn't obvious from "
    "the job posting.",
    "TONE": 'e.g. "confident but understated." Used if present, ignored if blank.',
    "RESUME_MAX_PAGES": "A rough length target for the tailored resume.",
    "AVOID": 'Words or phrasing to skip, e.g. "buzzwords, the word synergy."',
    "model": "Overrides the provider's default model. Leave blank unless you know the exact "
    "model name you want.",
    "download_config": "Saves your current settings — including your API key in plain text — "
    "as resume_match.env, so you can re-upload it next time instead of retyping everything. "
    "Keep the downloaded file private.",
    "credentials_upload": "Any mix of PDF, DOCX, TXT, MD, or image files (scanned "
    "diplomas/transcripts), plus an optional links.txt (one URL per line) and preferences.txt. "
    "A single .zip containing all of them works too.",
    "drive_credentials": "A link to a Google Drive folder shared as \"Anyone with the link can "
    "view.\" Fetches alongside anything you've already uploaded. Upload is the more reliable "
    "path — use this as a convenience, and fall back to upload if a fetch fails.",
    "fetch_drive": "Downloads every file in that folder and adds it to the list above. Nothing "
    "from the folder is kept on the server beyond this step.",
    "resume_selectbox": "More than one file here looks like a resume. Pick the one to treat as "
    "primary — the others are still read as supporting evidence.",
    "jobs_upload": "One file per posting works best. Postings from LinkedIn/Workday-style "
    "sites usually need to be saved as a file first (Print → Save as PDF) — see the README for "
    "why. A single .zip of all your postings works too.",
    "drive_jobs": "A link to a Google Drive folder of saved job postings, shared as \"Anyone "
    "with the link can view.\" Same convenience as the credentials one above.",
    "select_all": "Toggle every posting below on or off at once.",
    "generate_button": "Builds your credential profile once, then for each selected job: "
    "analyzes the posting, writes all seven documents, and checks them against your profile. "
    "Usually well under two minutes per job.",
    "download_doc": "Download this document as an editable .docx file.",
    "regenerate": "Re-runs this job from scratch: re-analyzes the posting and rewrites all "
    "seven documents plus the fidelity check. Replaces what's shown here; anything you already "
    "downloaded is unaffected.",
    "download_zip": "Every generated job's documents in one .zip, organized into one folder "
    "per job.",
    "start_over": "Clears everything in this session — your API key, uploaded files, and "
    "generated documents. This can't be undone; download anything you want to keep first.",
}


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header [data-testid="stToolbar"] {{visibility: hidden;}}

        html, body, [class*="css"] {{
            font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
            color: {TEXT_COLOR};
        }}

        body {{
            background-color: {BACKGROUND_COLOR};
        }}

        .block-container {{
            max-width: 780px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
        }}

        .sr-wordmark {{
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            color: {ACCENT_COLOR};
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }}

        .sr-title {{
            font-size: 2.1rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
            color: {TEXT_COLOR};
        }}

        .sr-tagline {{
            font-size: 1.05rem;
            color: {MUTED_TEXT_COLOR};
            margin-bottom: 0.9rem;
        }}

        .sr-rule {{
            height: 4px;
            width: 64px;
            border-radius: 4px;
            margin: 0.2rem 0 1.1rem 0;
            background: linear-gradient(90deg, {ACCENT_COLOR} 0%, {ACCENT_SOFT} 100%);
        }}

        .sr-free-app {{
            font-size: 0.85rem;
            color: {MUTED_TEXT_COLOR};
            margin-bottom: 0.9rem;
        }}

        .sr-free-app a {{
            color: {ACCENT_COLOR};
            text-decoration: none;
            border-bottom: 1px solid {ACCENT_SOFT};
            transition: border-color 0.15s ease;
        }}

        .sr-free-app a:hover {{
            border-color: {ACCENT_COLOR};
        }}

        .sr-privacy {{
            font-size: 0.88rem;
            color: {MUTED_TEXT_COLOR};
            background: {SURFACE_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 12px;
            padding: 0.7rem 1rem;
            margin-bottom: 2.25rem;
            box-shadow: 0 1px 3px rgba(193, 102, 46, 0.06);
        }}

        .sr-section-title {{
            font-size: 1.2rem;
            font-weight: 700;
            margin-top: 2.5rem;
            margin-bottom: 0.6rem;
            padding-left: 0.75rem;
            border-left: 4px solid {ACCENT_COLOR};
            color: {TEXT_COLOR};
        }}

        .sr-status-line {{
            font-size: 0.9rem;
            color: {MUTED_TEXT_COLOR};
            margin-bottom: 0.6rem;
        }}

        .sr-flag {{
            font-size: 0.88rem;
            background: #FDF1E2;
            border: 1px solid #F0C896;
            border-left: 3px solid {ACCENT_COLOR};
            border-radius: 8px;
            padding: 0.55rem 0.8rem;
            margin-bottom: 0.45rem;
        }}

        /* Buttons: warmer, a touch of lift on hover so the page feels responsive */
        div.stButton > button, div.stDownloadButton > button {{
            border-radius: 8px;
            border-color: {BORDER_COLOR};
            transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
        }}

        div.stButton > button:hover, div.stDownloadButton > button:hover {{
            transform: translateY(-1px);
            border-color: {ACCENT_COLOR};
            box-shadow: 0 3px 8px rgba(193, 102, 46, 0.15);
        }}

        div.stButton > button[kind="primary"] {{
            background-color: {ACCENT_COLOR};
            border-color: {ACCENT_COLOR};
        }}

        div.stButton > button[kind="primary"]:hover {{
            background-color: {ACCENT_DARK};
            border-color: {ACCENT_DARK};
            box-shadow: 0 4px 10px rgba(162, 79, 31, 0.3);
        }}

        /* Tabs: make the active tab feel warm rather than a thin grey line */
        button[data-baseweb="tab"] {{
            transition: color 0.12s ease;
        }}

        button[data-baseweb="tab"]:hover {{
            color: {ACCENT_COLOR};
        }}

        [data-baseweb="tab-highlight"] {{
            background-color: {ACCENT_COLOR} !important;
        }}

        /* Expanders: soften the box and warm it on hover */
        details {{
            border-radius: 10px !important;
        }}

        summary:hover {{
            color: {ACCENT_COLOR};
        }}

        hr {{
            border-color: {BORDER_COLOR};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(f'<div class="sr-wordmark">{WORDMARK_TEXT}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sr-title">{APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sr-rule"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sr-tagline">{APP_TAGLINE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sr-free-app">{FREE_APP_LINE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sr-privacy">{PRIVACY_LINE}</div>', unsafe_allow_html=True)


def section_title(text: str) -> None:
    st.markdown(f'<div class="sr-section-title">{text}</div>', unsafe_allow_html=True)


def status_line(text: str) -> None:
    st.markdown(f'<div class="sr-status-line">{text}</div>', unsafe_allow_html=True)


def fidelity_flag(text: str) -> None:
    st.markdown(f'<div class="sr-flag">⚑ {text}</div>', unsafe_allow_html=True)


def value_kw(widget_key: str, value) -> dict:
    """Avoid Streamlit's "value ignored, using session_state" warning: only pass an
    explicit default for a widget that doesn't already have a stored value (from
    an auto-loaded or uploaded config) — see session.load_config_values()."""
    return {} if widget_key in st.session_state else {"value": value}


def index_kw(widget_key: str, index: int) -> dict:
    """Same as value_kw(), for widgets (like st.radio) that take `index=` instead."""
    return {} if widget_key in st.session_state else {"index": index}
