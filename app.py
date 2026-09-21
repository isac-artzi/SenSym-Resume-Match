"""SenSym Resume Match — Streamlit entry point.

Layout only: this file wires widgets to `resume_match/` functions and reads
per-session state from `resume_match/session.py`. Extraction, prompting, and
rendering all live in the other modules; nothing here talks to a model or a
file format directly. Tooltip copy lives in `ui.TOOLTIPS` to keep this file
focused on wiring rather than prose.
"""

from __future__ import annotations

import streamlit as st

from resume_match import config as config_mod
from resume_match import pipeline, render, session, ui
from resume_match.llm import LLMError

st.set_page_config(page_title=ui.APP_NAME, layout="centered")
ui.inject_css()

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TT = ui.TOOLTIPS


# --- Section 1: Setup -------------------------------------------------------


def render_setup(cfg: config_mod.AppConfig, mode: str) -> None:
    ui.section_title("1. Setup")
    upload_tab, form_tab = st.tabs(["Upload a config file", "Fill in the form"])

    with upload_tab:
        uploaded = st.file_uploader(
            "resume_match.env", type=["env", "txt"], key="config_upload", help=TT["config_upload"]
        )
        if uploaded is not None:
            st.session_state.config_values.update(config_mod.parse_env_text(uploaded.getvalue().decode("utf-8")))
            st.success("Config loaded for this session.")

    with form_tab:
        provider = st.radio(
            "AI provider",
            config_mod.PROVIDERS,
            index=config_mod.PROVIDERS.index(cfg.provider) if cfg.provider in config_mod.PROVIDERS else 0,
            horizontal=True,
            key="form_provider",
            help=TT["provider"],
        )
        st.session_state.config_values["LLM_PROVIDER"] = provider

        if provider != "ollama":
            api_key = st.text_input(
                "API key", value=cfg.api_key, type="password", key="form_api_key", help=TT["api_key"]
            )
            st.session_state.config_values["API_KEY"] = api_key
        else:
            st.session_state.config_values["API_KEY"] = ""
            ollama_url = st.text_input(
                "Ollama base URL", value=cfg.ollama_base_url, key="form_ollama_url", help=TT["ollama_url"]
            )
            st.session_state.config_values["OLLAMA_BASE_URL"] = ollama_url

        if mode == "local":
            st.caption("Folder paths (local mode)")
            for label, key, default in [
                ("Credentials folder", "CREDENTIALS_DIR", "examples/credentials"),
                ("Jobs folder", "JOBS_DIR", "examples/jobs"),
                ("Output folder", "OUTPUT_DIR", "applications"),
            ]:
                value = st.text_input(label, value=cfg.get(key, default), key=f"form_{key}", help=TT[key])
                st.session_state.config_values[key] = value

        with st.expander("Preferences (optional)"):
            for label, key in [
                ("Your name", "STUDENT_NAME"),
                ("Target role", "TARGET_ROLE"),
                ("Tone", "TONE"),
                ("Resume max pages", "RESUME_MAX_PAGES"),
                ("Things to avoid", "AVOID"),
            ]:
                value = st.text_input(label, value=cfg.get(key), key=f"form_{key}", help=TT[key])
                st.session_state.config_values[key] = value

        with st.expander("Advanced", expanded=False):
            model = st.text_input(
                "Model (blank = provider default)", value=cfg.model, key="form_model", help=TT["model"]
            )
            st.session_state.config_values["MODEL"] = model

        st.download_button(
            "Download config",
            data=config_mod.generate_env_text(st.session_state.config_values),
            file_name="resume_match.env",
            mime="text/plain",
            help=TT["download_config"],
        )


# --- Section 2: Materials ---------------------------------------------------


def render_drive_fetch(cfg: config_mod.AppConfig, config_key: str, session_key: str, tooltip_key: str) -> None:
    """A link field + fetch button for an optional public Google Drive folder.
    Fetched files land in st.session_state[session_key] and get merged in by the caller."""
    url = st.text_input(
        "Or fetch from a public Google Drive folder link",
        value=cfg.get(config_key, ""),
        key=f"{config_key}_input",
        placeholder="https://drive.google.com/drive/folders/...",
        help=TT[tooltip_key],
    )
    st.session_state.config_values[config_key] = url
    if st.button("Fetch from Drive", key=f"fetch_{session_key}", disabled=not url.strip(), help=TT["fetch_drive"]):
        session.fetch_drive(session_key, url)


def render_materials(mode: str, cfg: config_mod.AppConfig) -> list[tuple[str, bytes]]:
    ui.section_title("2. Your materials")

    if mode == "local":
        files = session.read_local_folder(cfg.credentials_dir(), session.CREDENTIAL_EXTS)
        ui.status_line(f"Reading from `{cfg.credentials_dir()}`")
    else:
        uploaded = st.file_uploader(
            "Resume, transcripts, diplomas, links.txt, preferences.txt — files or a .zip",
            accept_multiple_files=True,
            key="credentials_upload",
            help=TT["credentials_upload"],
        )
        render_drive_fetch(cfg, "DRIVE_CREDENTIALS_URL", "drive_credential_files", "drive_credentials")
        files = session.expand_uploads(uploaded) + st.session_state.drive_credential_files

    if files:
        names = [name for name, _ in files]
        n_links = sum(1 for n in names if n.lower().endswith("links.txt"))
        candidates = [n for n in names if "resume" in n.lower() or "cv" in n.lower()]
        resume_note = f"resume: {candidates[0]}" if candidates else "no resume detected"
        if len(candidates) > 1:
            chosen = st.selectbox(
                "Multiple resumes found — pick the base one", candidates, help=TT["resume_selectbox"]
            )
            st.session_state.selected_resume = chosen
            resume_note = f"resume: {chosen}"
        ui.status_line(f"{len(files)} files, {n_links} link file(s) · {resume_note}")
    else:
        st.info("No credential files found yet.")

    return files


# --- Section 3: Jobs ---------------------------------------------------------


def render_jobs(mode: str, cfg: config_mod.AppConfig) -> list[tuple[str, bytes]]:
    ui.section_title("3. Jobs")

    if mode == "local":
        files = session.read_local_folder(cfg.jobs_dir(), session.JOB_EXTS)
    else:
        uploaded = st.file_uploader(
            "One file per job posting — .pdf, .docx, .txt, .md, or a .zip",
            accept_multiple_files=True,
            key="jobs_upload",
            help=TT["jobs_upload"],
        )
        render_drive_fetch(cfg, "DRIVE_JOBS_URL", "drive_job_files", "drive_jobs")
        files = session.expand_uploads(uploaded) + st.session_state.drive_job_files

    if not files:
        st.info(
            "No job postings found yet. Postings on LinkedIn, Workday, and similar sites sit "
            "behind logins or dynamic pages that can't be fetched reliably — save the posting "
            "as a file (Print -> Save as PDF, or copy-paste into a .txt) and add it here."
        )
        return []

    select_all = st.checkbox("Select all", value=True, key="select_all_jobs", help=TT["select_all"])
    selected = []
    for name, data in files:
        if st.checkbox(name, value=select_all, key=f"job_check_{name}", help=f"Include {name} in this batch."):
            selected.append((name, data))
    return selected


# --- Section 4: Generate -----------------------------------------------------


def render_generate(
    cfg: config_mod.AppConfig,
    credential_files: list[tuple[str, bytes]],
    selected_jobs: list[tuple[str, bytes]],
) -> None:
    ui.section_title("4. Generate")

    if credential_files and selected_jobs:
        llm_config = session.current_llm_config(cfg)
        if llm_config.provider == "ollama":
            st.caption("Ollama runs on your own computer — no per-token cost, just your own compute time.")
        else:
            estimate = session.get_cost_estimate(cfg, credential_files, selected_jobs)
            st.caption(
                f"Estimated cost: ~${estimate['cost_usd']:.2f} for {len(selected_jobs)} job(s) on "
                f"{llm_config.provider} ({llm_config.resolved_model()}) — roughly "
                f"{estimate['input_tokens']:,} input and {estimate['output_tokens']:,} output tokens. "
                "This is a rough estimate, not a bill — actual cost depends on your documents."
            )
    else:
        st.caption("Add materials and select at least one job to see a cost estimate here.")

    problems = config_mod.validate(cfg)
    disabled = bool(problems) or not credential_files or not selected_jobs
    if st.button(
        "Create application materials", type="primary", disabled=disabled, help=TT["generate_button"]
    ):
        session.run_generation(cfg, credential_files, selected_jobs)
        st.rerun()

    for problem in problems:
        st.caption(f"⚑ {problem}")
    if not credential_files:
        st.caption("⚑ Add at least one credential file first.")
    if not selected_jobs:
        st.caption("⚑ Select at least one job first.")


# --- Section 5: Review -------------------------------------------------------


def show_gap_analysis(gap: dict) -> None:
    st.write(gap.get("match_summary", ""))
    col_met, col_partial, col_gap = st.columns(3)
    with col_met:
        st.markdown("**Met**")
        for item in gap.get("met", []):
            st.write(f"- {item}")
    with col_partial:
        st.markdown("**Partially met**")
        for item in gap.get("partially_met", []):
            st.write(f"- {item.get('requirement', '')}: {item.get('note', '')}")
    with col_gap:
        st.markdown("**Gap**")
        for item in gap.get("gaps", []):
            st.write(f"- {item.get('requirement', '')}")
            st.caption(f"Study: {item.get('study_suggestion', '')}")
            st.caption(f"Do: {item.get('action_suggestion', '')}")
            st.caption(f"Time: {item.get('estimated_time', '')}")


def render_review(cfg: config_mod.AppConfig, mode: str) -> None:
    results = st.session_state.results
    if not results:
        return

    ui.section_title("5. Review")
    job_tabs = st.tabs([r["job_analysis"].get("company", name) for name, r in results.items()])

    for job_tab, (folder_name, entry) in zip(job_tabs, results.items()):
        with job_tab:
            job_analysis = entry["job_analysis"]
            st.caption(f"{job_analysis.get('role', '')} · {job_analysis.get('company', '')}")

            flags_by_doc: dict[str, list] = {}
            for flag in entry["fidelity"].get("flags", []):
                flags_by_doc.setdefault(flag.get("document"), []).append(flag)

            doc_keys = list(render.DOCUMENT_LABELS)
            doc_tabs = st.tabs([render.DOCUMENT_LABELS[key] for key in doc_keys])
            for doc_tab, doc_key in zip(doc_tabs, doc_keys):
                with doc_tab:
                    for flag in flags_by_doc.get(doc_key, []):
                        ui.fidelity_flag(f"{flag.get('claim', '')} — {flag.get('reason', '')}")

                    if doc_key == "gap_analysis":
                        show_gap_analysis(entry["bundle"].get("gap_analysis", {}))
                    else:
                        st.text(pipeline.document_preview_text(doc_key, entry["bundle"]))

                    st.download_button(
                        "Download",
                        data=entry["files"][f"{doc_key}.docx"],
                        file_name=f"{doc_key}.docx",
                        mime=DOCX_MIME,
                        key=f"download_{folder_name}_{doc_key}",
                        help=TT["download_doc"],
                    )

            if st.button(
                "Regenerate this job's documents", key=f"regen_{folder_name}", help=TT["regenerate"]
            ):
                try:
                    session.regenerate_job(cfg, entry)
                except LLMError as exc:
                    st.error(str(exc))
                else:
                    st.rerun()

    st.divider()
    if mode == "cloud":
        zip_bytes = render.build_zip({name: entry["files"] for name, entry in results.items()})
        st.download_button(
            "Download everything (.zip)",
            data=zip_bytes,
            file_name="applications.zip",
            mime="application/zip",
            help=TT["download_zip"],
        )
    else:
        st.caption(f"Saved to {cfg.output_dir()}")

    if st.button("Start over", help=TT["start_over"]):
        st.session_state.clear()
        st.rerun()


# --- Main --------------------------------------------------------------------


def main() -> None:
    session.init_state()
    ui.render_header()

    cfg = session.current_config()
    mode = config_mod.detect_mode(cfg)

    render_setup(cfg, mode)
    cfg = session.current_config()  # re-read after form edits
    mode = config_mod.detect_mode(cfg)

    credential_files = render_materials(mode, cfg)
    selected_jobs = render_jobs(mode, cfg)
    render_generate(cfg, credential_files, selected_jobs)
    render_review(cfg, mode)


main()
