"""The four-step generation pipeline: profile -> job analysis -> bundle -> fidelity check.

Every step is a single `complete_json()` call against a prompt template in
`prompts/`. Templates use `$name` placeholders (Python's `string.Template`)
rather than `str.format`, because the prompts contain literal JSON examples
full of `{`/`}` that `.format()` would try to parse as fields.
"""

from __future__ import annotations

import json
from pathlib import Path
from string import Template

from resume_match.llm import LLMConfig, complete_json

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

RETURN_JSON_ONLY = "Return only the JSON object specified above. No prose, no markdown fences."


def _load_prompt(name: str) -> Template:
    return Template((PROMPTS_DIR / name).read_text(encoding="utf-8"))


def build_profile(source_text: str, preferences_text: str, llm_config: LLMConfig) -> dict:
    """Step 2: one call, reused across every job in the batch."""
    prompt = _load_prompt("profile.txt").substitute(
        source_text=source_text or "(no source material provided)",
        preferences_text=preferences_text or "(none provided)",
    )
    return complete_json(llm_config, prompt, RETURN_JSON_ONLY)


def analyze_job(job_filename: str, job_text: str, llm_config: LLMConfig) -> dict:
    """Step 3: one call per job."""
    prompt = _load_prompt("job_analysis.txt").substitute(
        job_filename=job_filename,
        job_text=job_text,
    )
    return complete_json(llm_config, prompt, RETURN_JSON_ONLY)


def generate_bundle(profile: dict, job_analysis: dict, preferences_text: str, llm_config: LLMConfig) -> dict:
    """Step 4: one call per job, producing all seven documents as JSON."""
    prompt = _load_prompt("bundle.txt").substitute(
        profile_json=json.dumps(profile, indent=2),
        job_analysis_json=json.dumps(job_analysis, indent=2),
        preferences_text=preferences_text or "(none provided)",
    )
    return complete_json(llm_config, prompt, RETURN_JSON_ONLY)


def fidelity_check(profile: dict, bundle: dict, llm_config: LLMConfig) -> dict:
    """Step 5: compare the resume and cover letter against the profile."""
    prompt = _load_prompt("fidelity_check.txt").substitute(
        profile_json=json.dumps(profile, indent=2),
        resume_text=resume_to_text(bundle.get("resume", {})),
        cover_letter_text=cover_letter_to_text(bundle.get("cover_letter", {})),
    )
    return complete_json(llm_config, prompt, RETURN_JSON_ONLY)


def resume_to_text(resume: dict) -> str:
    """Flatten the structured resume into plain text, for the fidelity check
    prompt and for the in-app preview."""
    lines = []
    if resume.get("summary"):
        lines.append(resume["summary"])
        lines.append("")

    if resume.get("experience"):
        lines.append("EXPERIENCE")
        for job in resume["experience"]:
            header = f"{job.get('title', '')} — {job.get('organization', '')} ({job.get('dates', '')})"
            lines.append(header)
            for bullet in job.get("bullets", []):
                lines.append(f"  - {bullet}")
        lines.append("")

    if resume.get("education"):
        lines.append("EDUCATION")
        for edu in resume["education"]:
            lines.append(f"{edu.get('credential', '')} — {edu.get('institution', '')}")
            if edu.get("details"):
                lines.append(f"  {edu['details']}")
        lines.append("")

    if resume.get("projects"):
        lines.append("PROJECTS")
        for project in resume["projects"]:
            lines.append(f"{project.get('name', '')}: {project.get('description', '')}")
        lines.append("")

    if resume.get("skills"):
        lines.append("SKILLS: " + ", ".join(resume["skills"]))

    if resume.get("certifications"):
        lines.append("CERTIFICATIONS: " + ", ".join(resume["certifications"]))

    return "\n".join(lines)


def cover_letter_to_text(cover_letter: dict) -> str:
    parts = [cover_letter.get("greeting", "")]
    parts.extend(cover_letter.get("body_paragraphs", []))
    parts.append(cover_letter.get("closing", ""))
    return "\n\n".join(p for p in parts if p)


def document_preview_text(doc_key: str, bundle: dict) -> str:
    """Flatten any one of the seven bundle documents to plain text, for the
    review panel's preview pane."""
    if doc_key == "resume":
        return resume_to_text(bundle.get("resume", {}))
    if doc_key == "cover_letter":
        return cover_letter_to_text(bundle.get("cover_letter", {}))
    if doc_key == "intro_email":
        email = bundle.get("intro_email", {})
        return f"Subject: {email.get('subject', '')}\n\n{email.get('body', '')}"
    if doc_key == "linkedin_message":
        return bundle.get("linkedin_message", {}).get("body", "")
    if doc_key == "elevator_pitch":
        return bundle.get("elevator_pitch", {}).get("text", "")
    if doc_key == "interview_prep":
        prep = bundle.get("interview_prep", {})
        lines = []
        for item in prep.get("likely_questions", []):
            lines.append(item.get("question", ""))
            lines.extend(f"  - {p}" for p in item.get("talking_points", []))
        if prep.get("questions_to_ask"):
            lines.append("\nQuestions to ask:")
            lines.extend(f"  - {q}" for q in prep["questions_to_ask"])
        return "\n".join(lines)
    return ""


def run_for_job(
    profile: dict,
    job_filename: str,
    job_text: str,
    preferences_text: str,
    llm_config: LLMConfig,
) -> dict:
    """Run steps 3-5 for a single job and return everything the review UI needs."""
    job_analysis = analyze_job(job_filename, job_text, llm_config)
    bundle = generate_bundle(profile, job_analysis, preferences_text, llm_config)
    fidelity = fidelity_check(profile, bundle, llm_config)
    return {
        "job_analysis": job_analysis,
        "bundle": bundle,
        "fidelity": fidelity,
    }
