"""Brand tokens, CSS, and small UI helpers.

Everything visual lives here so a real SenSym logo/color can replace the
neutral placeholder later by editing this one file.
"""

from __future__ import annotations

import streamlit as st

ACCENT_COLOR = "#4B5A64"
TEXT_COLOR = "#1A1A1A"
MUTED_TEXT_COLOR = "#6B6B68"
BACKGROUND_COLOR = "#FFFFFF"
SURFACE_COLOR = "#F7F7F5"
BORDER_COLOR = "#E4E4E0"

APP_NAME = "SenSym Resume Match"
APP_TAGLINE = "Turn your credentials and a job posting into a submission-ready application bundle."
PRIVACY_LINE = (
    "Nothing you upload is stored or tracked. Everything lives in your browser "
    "session and disappears when you close it."
)

SENSYM_URL = "https://sensym.ai"
WORDMARK_TEXT = "SenSym™"  # TODO: replace with the real SVG wordmark once brand assets arrive
FREE_APP_LINE = f'A free app from SenSym™ — <a href="{SENSYM_URL}" target="_blank" rel="noopener">sensym.ai</a>'


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

        .block-container {{
            max-width: 780px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
        }}

        .sr-wordmark {{
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            color: {ACCENT_COLOR};
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }}

        .sr-title {{
            font-size: 2rem;
            font-weight: 650;
            margin-bottom: 0.35rem;
            color: {TEXT_COLOR};
        }}

        .sr-tagline {{
            font-size: 1.02rem;
            color: {MUTED_TEXT_COLOR};
            margin-bottom: 1rem;
        }}

        .sr-free-app {{
            font-size: 0.85rem;
            color: {MUTED_TEXT_COLOR};
            margin-bottom: 0.75rem;
        }}

        .sr-free-app a {{
            color: {ACCENT_COLOR};
            text-decoration: none;
            border-bottom: 1px solid {BORDER_COLOR};
        }}

        .sr-privacy {{
            font-size: 0.88rem;
            color: {MUTED_TEXT_COLOR};
            background: {SURFACE_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 0.6rem 0.9rem;
            margin-bottom: 2rem;
        }}

        .sr-section-title {{
            font-size: 1.15rem;
            font-weight: 650;
            margin-top: 2.25rem;
            margin-bottom: 0.4rem;
            color: {TEXT_COLOR};
        }}

        .sr-status-line {{
            font-size: 0.9rem;
            color: {MUTED_TEXT_COLOR};
            margin-bottom: 0.6rem;
        }}

        .sr-flag {{
            font-size: 0.88rem;
            background: #FBF3E8;
            border: 1px solid #EAD9BC;
            border-radius: 6px;
            padding: 0.5rem 0.75rem;
            margin-bottom: 0.4rem;
        }}

        div.stButton > button[kind="primary"] {{
            background-color: {ACCENT_COLOR};
            border-color: {ACCENT_COLOR};
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
    st.markdown(f'<div class="sr-tagline">{APP_TAGLINE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sr-free-app">{FREE_APP_LINE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sr-privacy">{PRIVACY_LINE}</div>', unsafe_allow_html=True)


def section_title(text: str) -> None:
    st.markdown(f'<div class="sr-section-title">{text}</div>', unsafe_allow_html=True)


def status_line(text: str) -> None:
    st.markdown(f'<div class="sr-status-line">{text}</div>', unsafe_allow_html=True)


def fidelity_flag(text: str) -> None:
    st.markdown(f'<div class="sr-flag">⚑ {text}</div>', unsafe_allow_html=True)
