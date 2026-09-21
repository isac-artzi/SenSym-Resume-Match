"""Per-session state and the generate/regenerate actions.

Split out of `app.py` so that file can stay a readable layout script. This
module still touches `st.session_state` and shows generation progress
(there is no clean way to run a multi-step model pipeline from a button
click without some UI feedback woven in) but it never lays out a page
section — that stays in `app.py`.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import streamlit as st

from resume_match import config as config_mod
from resume_match import cost, drive, ingest, pipeline, render
from resume_match.drive import DriveFetchError
from resume_match.llm import LLMConfig, LLMError

REPO_ROOT = Path(__file__).resolve().parent.parent
CREDENTIAL_EXTS = {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"}
JOB_EXTS = {".pdf", ".docx", ".txt", ".md"}

# Maps each config key to the Setup form widget that displays it, so
# load_config_values() can keep both in sync — see its docstring for why
# that's necessary.
FORM_WIDGET_KEYS = {
    "LLM_PROVIDER": "form_provider",
    "API_KEY": "form_api_key",
    "OLLAMA_BASE_URL": "form_ollama_url",
    "MODEL": "form_model",
    "CREDENTIALS_DIR": "form_CREDENTIALS_DIR",
    "JOBS_DIR": "form_JOBS_DIR",
    "OUTPUT_DIR": "form_OUTPUT_DIR",
    "STUDENT_NAME": "form_STUDENT_NAME",
    "TARGET_ROLE": "form_TARGET_ROLE",
    "TONE": "form_TONE",
    "RESUME_MAX_PAGES": "form_RESUME_MAX_PAGES",
    "AVOID": "form_AVOID",
    "DRIVE_CREDENTIALS_URL": "DRIVE_CREDENTIALS_URL_input",
    "DRIVE_JOBS_URL": "DRIVE_JOBS_URL_input",
}


def init_state() -> None:
    defaults = {
        "config_values": {},
        "env_autoloaded": False,
        "selected_resume": None,
        "profile": None,
        "profile_source_key": None,
        "results": {},  # job_folder_name -> {source_name, job_text, job_analysis, bundle, fidelity, files}
        "drive_credential_files": [],  # (filename, bytes) fetched from a public Drive folder
        "drive_job_files": [],
        "cost_estimate": None,
        "cost_estimate_key": None,
        "config_upload_id": None,  # last-processed uploaded config's file_id, to avoid reprocessing
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    if not st.session_state.env_autoloaded:
        local_env = config_mod.load_env_file(REPO_ROOT / "resume_match.env")
        if local_env:
            load_config_values(local_env)
        st.session_state.env_autoloaded = True


def load_config_values(parsed: dict) -> None:
    """Merge parsed config values into session state, including the Setup
    form's widget-backed keys.

    Necessary because a Streamlit widget created with a `key=` ignores its
    `value=`/`index=` argument on every render after the first — and the
    "Fill in the form" tab's widgets are created on every run regardless of
    which tab is visible (`st.tabs()` still executes hidden tab content).
    Updating `config_values` alone therefore doesn't change what those
    widgets show; on the very next line they'd read their own stale
    session-state value and immediately overwrite config_values with it.
    Setting each widget's session_state key directly, before that widget is
    (re-)created, is what actually takes effect — this must run before
    render_setup() so the values exist first.
    """
    st.session_state.config_values.update(parsed)
    for config_key, widget_key in FORM_WIDGET_KEYS.items():
        if config_key in parsed:
            st.session_state[widget_key] = parsed[config_key]


def current_config() -> config_mod.AppConfig:
    return config_mod.AppConfig(values=st.session_state.config_values)


def current_llm_config(cfg: config_mod.AppConfig) -> LLMConfig:
    return LLMConfig(
        provider=cfg.provider,
        api_key=cfg.api_key,
        model=cfg.model,
        ollama_base_url=cfg.ollama_base_url,
    )


def expand_uploads(uploaded_files) -> list[tuple[str, bytes]]:
    """Flatten Streamlit uploads into (filename, bytes), unzipping any .zip."""
    files: list[tuple[str, bytes]] = []
    for uploaded in uploaded_files or []:
        data = uploaded.getvalue()
        if uploaded.name.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    files.append((info.filename, zf.read(info)))
        else:
            files.append((uploaded.name, data))
    return files


def read_local_folder(folder: Path, allowed_exts: set[str]) -> list[tuple[str, bytes]]:
    if folder is None or not folder.is_dir():
        return []
    files = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and (path.suffix.lower() in allowed_exts or path.name.lower() == "links.txt"):
            files.append((path.name, path.read_bytes()))
    return files


def run_generation(
    cfg: config_mod.AppConfig,
    mode: str,
    credential_files: list[tuple[str, bytes]],
    selected_jobs: list[tuple[str, bytes]],
) -> None:
    """The Generate button's action: profile once, then per-job analyze/write/check/render.

    Every per-job failure — model error or anything else — is caught, shown
    with `st.error()`, and the batch moves on to the next job rather than
    stopping silently. (A prior version of this app called `st.rerun()`
    right after this function returned, which wiped any error shown here
    before it could be read — fixed by not doing that; see app.py.)
    """
    llm_config = current_llm_config(cfg)
    progress = st.progress(0.0)
    status = st.empty()

    status.text("Reading credentials...")
    result, extra_preferences = ingest.gather_credentials(credential_files, llm_config)
    for warning in result.warnings:
        st.warning(warning)
    source_text = result.combined_text()
    preferences_text = "\n".join(p for p in [cfg.preferences_text(), extra_preferences] if p)

    source_key = hash((source_text, preferences_text, cfg.provider, cfg.model))
    if st.session_state.profile is None or st.session_state.profile_source_key != source_key:
        status.text("Building your credential profile...")
        try:
            st.session_state.profile = pipeline.build_profile(source_text, preferences_text, llm_config)
            st.session_state.profile_source_key = source_key
        except Exception as exc:  # noqa: BLE001 - any failure here must be visible, not silent
            st.error(str(exc) if isinstance(exc, LLMError) else f"Could not build your credential profile: {exc}")
            return
    profile = st.session_state.profile

    total = len(selected_jobs)
    for i, (job_name, job_data) in enumerate(selected_jobs):
        status.text(f"[{i + 1}/{total}] {job_name}: analyzing...")
        job_ingest = ingest.ingest_files([(job_name, job_data)])
        if not job_ingest.sources:
            st.warning(f"Could not read {job_name}, skipped.")
            progress.progress((i + 1) / total)
            continue
        job_text = job_ingest.sources[0].text

        try:
            job_analysis = pipeline.analyze_job(job_name, job_text, llm_config)
            status.text(f"[{i + 1}/{total}] {job_analysis.get('company', job_name)}: writing documents...")
            bundle = pipeline.generate_bundle(profile, job_analysis, preferences_text, llm_config)
            status.text(f"[{i + 1}/{total}] {job_analysis.get('company', job_name)}: checking fidelity...")
            fidelity = pipeline.fidelity_check(profile, bundle, llm_config)
            status.text(f"[{i + 1}/{total}] {job_analysis.get('company', job_name)}: rendering...")
            files = render.render_all(profile, job_analysis, bundle, fidelity)
            save_result(cfg, mode, job_name, job_text, job_analysis, bundle, fidelity, files)
        except Exception as exc:  # noqa: BLE001 - one bad job must not silently end the batch
            st.error(f"{job_name}: {exc if isinstance(exc, LLMError) else f'unexpected error — {exc}'}")
        progress.progress((i + 1) / total)

    status.text("Done.")


def save_result(cfg, mode: str, source_name, job_text, job_analysis, bundle, fidelity, files) -> str:
    folder_name = render.job_folder_name(job_analysis.get("company", ""), job_analysis.get("role", ""))
    st.session_state.results[folder_name] = {
        "source_name": source_name,
        "job_text": job_text,
        "job_analysis": job_analysis,
        "bundle": bundle,
        "fidelity": fidelity,
        "files": files,
    }
    output_dir = cfg.output_dir()
    if mode == "local" and output_dir is not None:
        render.write_to_folder(files, output_dir, job_analysis.get("company", ""), job_analysis.get("role", ""))
    return folder_name


def regenerate_job(cfg: config_mod.AppConfig, mode: str, entry: dict) -> None:
    """Re-run analysis/bundle/fidelity/render for one job and overwrite its result."""
    llm_config = current_llm_config(cfg)
    updated = pipeline.run_for_job(
        st.session_state.profile,
        entry["source_name"],
        entry["job_text"],
        cfg.preferences_text(),
        llm_config,
    )
    files = render.render_all(
        st.session_state.profile, updated["job_analysis"], updated["bundle"], updated["fidelity"]
    )
    save_result(
        cfg,
        mode,
        entry["source_name"],
        entry["job_text"],
        updated["job_analysis"],
        updated["bundle"],
        updated["fidelity"],
        files,
    )


def fetch_drive(session_key: str, url: str) -> None:
    """The Drive-fetch button's action: download and store, or show a friendly error."""
    try:
        with st.spinner("Fetching from Google Drive..."):
            fetched = drive.fetch_drive_folder(url)
    except DriveFetchError as exc:
        st.error(str(exc))
    else:
        st.session_state[session_key] = fetched
        st.success(f"Fetched {len(fetched)} file(s) from Drive.")


def get_cost_estimate(
    cfg: config_mod.AppConfig,
    credential_files: list[tuple[str, bytes]],
    selected_jobs: list[tuple[str, bytes]],
) -> dict:
    """Cost estimate for the current materials/jobs, cached in session_state
    so files aren't re-parsed on every unrelated widget interaction."""
    llm_config = current_llm_config(cfg)
    cache_key = (
        tuple((n, len(d)) for n, d in credential_files),
        tuple((n, len(d)) for n, d in selected_jobs),
        llm_config.provider,
    )
    if st.session_state.cost_estimate_key != cache_key:
        st.session_state.cost_estimate = cost.estimate_cost(llm_config, credential_files, selected_jobs)
        st.session_state.cost_estimate_key = cache_key
    return st.session_state.cost_estimate
