"""Render a generated document bundle to clean, ATS-friendly DOCX files.

Single column, standard heading styles, no tables or text boxes, system
fonts — the kind of resume an applicant-tracking system can actually parse.
`application.json` is written alongside so students can re-render or build on
the structured data without calling the model again.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

import docx
from docx.shared import Pt

BODY_FONT = "Calibri"
BODY_SIZE = Pt(11)

# Canonical document order and display labels, shared by the renderer and the
# review UI so there is one place that knows what the seven documents are.
DOCUMENT_LABELS = {
    "resume": "Resume",
    "cover_letter": "Cover Letter",
    "intro_email": "Intro Email",
    "linkedin_message": "LinkedIn",
    "elevator_pitch": "Elevator Pitch",
    "interview_prep": "Interview Prep",
    "gap_analysis": "Gap Analysis",
}


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "untitled"


def job_folder_name(company: str, role: str) -> str:
    return f"{slugify(company)}-{slugify(role)}"


def _new_document() -> docx.Document:
    document = docx.Document()
    style = document.styles["Normal"]
    style.font.name = BODY_FONT
    style.font.size = BODY_SIZE
    for section in document.sections:
        section.left_margin = section.right_margin = docx.shared.Inches(1)
    return document


def _add_heading(document: docx.Document, text: str, level: int = 1) -> None:
    heading = document.add_heading(text, level=level)
    for run in heading.runs:
        run.font.name = BODY_FONT


def render_resume_docx(resume: dict, contact: dict) -> docx.Document:
    document = _new_document()
    _add_heading(document, contact.get("name") or "Resume", level=0)

    contact_line = " | ".join(
        v for v in [contact.get("email"), contact.get("phone"), contact.get("location")] if v
    )
    if contact_line:
        document.add_paragraph(contact_line)
    for link in contact.get("links", []) or []:
        document.add_paragraph(link)

    if resume.get("summary"):
        _add_heading(document, "Summary", level=1)
        document.add_paragraph(resume["summary"])

    if resume.get("experience"):
        _add_heading(document, "Experience", level=1)
        for job in resume["experience"]:
            header = document.add_paragraph()
            header.add_run(f"{job.get('title', '')} — {job.get('organization', '')}").bold = True
            if job.get("dates"):
                header.add_run(f"  ({job['dates']})")
            for bullet in job.get("bullets", []):
                document.add_paragraph(bullet, style="List Bullet")

    if resume.get("education"):
        _add_heading(document, "Education", level=1)
        for edu in resume["education"]:
            para = document.add_paragraph()
            para.add_run(f"{edu.get('credential', '')} — {edu.get('institution', '')}").bold = True
            if edu.get("details"):
                document.add_paragraph(edu["details"])

    if resume.get("projects"):
        _add_heading(document, "Projects", level=1)
        for project in resume["projects"]:
            para = document.add_paragraph()
            para.add_run(f"{project.get('name', '')}: ").bold = True
            para.add_run(project.get("description", ""))

    if resume.get("skills"):
        _add_heading(document, "Skills", level=1)
        document.add_paragraph(", ".join(resume["skills"]))

    if resume.get("certifications"):
        _add_heading(document, "Certifications", level=1)
        document.add_paragraph(", ".join(resume["certifications"]))

    return document


def render_cover_letter_docx(cover_letter: dict, contact: dict, company: str, role: str) -> docx.Document:
    document = _new_document()
    if contact.get("name"):
        document.add_paragraph(contact["name"])
    _add_heading(document, f"Cover Letter — {role} at {company}", level=1)
    if cover_letter.get("greeting"):
        document.add_paragraph(cover_letter["greeting"])
    for paragraph in cover_letter.get("body_paragraphs", []):
        document.add_paragraph(paragraph)
    if cover_letter.get("closing"):
        document.add_paragraph(cover_letter["closing"])
    return document


def render_intro_email_docx(intro_email: dict) -> docx.Document:
    document = _new_document()
    _add_heading(document, "Introduction Email", level=1)
    if intro_email.get("subject"):
        subject = document.add_paragraph()
        subject.add_run("Subject: ").bold = True
        subject.add_run(intro_email["subject"])
    document.add_paragraph(intro_email.get("body", ""))
    return document


def render_linkedin_message_docx(linkedin_message: dict) -> docx.Document:
    document = _new_document()
    _add_heading(document, "LinkedIn Message", level=1)
    document.add_paragraph(linkedin_message.get("body", ""))
    return document


def render_elevator_pitch_docx(elevator_pitch: dict) -> docx.Document:
    document = _new_document()
    _add_heading(document, "Elevator Pitch", level=1)
    document.add_paragraph(elevator_pitch.get("text", ""))
    return document


def render_interview_prep_docx(interview_prep: dict) -> docx.Document:
    document = _new_document()
    _add_heading(document, "Interview Prep", level=1)

    _add_heading(document, "Likely Questions", level=2)
    for item in interview_prep.get("likely_questions", []):
        para = document.add_paragraph()
        para.add_run(item.get("question", "")).bold = True
        for point in item.get("talking_points", []):
            document.add_paragraph(point, style="List Bullet")

    if interview_prep.get("questions_to_ask"):
        _add_heading(document, "Questions to Ask", level=2)
        for question in interview_prep["questions_to_ask"]:
            document.add_paragraph(question, style="List Bullet")

    return document


def render_gap_analysis_docx(gap_analysis: dict) -> docx.Document:
    document = _new_document()
    _add_heading(document, "Gap Analysis", level=1)

    if gap_analysis.get("match_summary"):
        document.add_paragraph(gap_analysis["match_summary"])

    if gap_analysis.get("met"):
        _add_heading(document, "You meet", level=2)
        for item in gap_analysis["met"]:
            document.add_paragraph(item, style="List Bullet")

    if gap_analysis.get("partially_met"):
        _add_heading(document, "You partially meet", level=2)
        for item in gap_analysis["partially_met"]:
            para = document.add_paragraph(style="List Bullet")
            para.add_run(f"{item.get('requirement', '')}: ").bold = True
            para.add_run(item.get("note", ""))

    if gap_analysis.get("gaps"):
        _add_heading(document, "Gaps and how to close them", level=2)
        for gap in gap_analysis["gaps"]:
            para = document.add_paragraph()
            para.add_run(gap.get("requirement", "")).bold = True
            document.add_paragraph(f"Study: {gap.get('study_suggestion', '')}", style="List Bullet")
            document.add_paragraph(f"Do: {gap.get('action_suggestion', '')}", style="List Bullet")
            if gap.get("estimated_time"):
                document.add_paragraph(f"Time: {gap['estimated_time']}", style="List Bullet")

    return document


def render_all(profile: dict, job_analysis: dict, bundle: dict, fidelity: dict) -> dict[str, bytes]:
    """Render every document in the bundle to DOCX bytes, plus application.json.

    Returns {filename: bytes}, ready to write to a folder or zip.
    """
    contact = profile.get("contact", {})
    company = job_analysis.get("company", "company")
    role = job_analysis.get("role", "role")

    documents = {
        "resume.docx": render_resume_docx(bundle.get("resume", {}), contact),
        "cover_letter.docx": render_cover_letter_docx(bundle.get("cover_letter", {}), contact, company, role),
        "intro_email.docx": render_intro_email_docx(bundle.get("intro_email", {})),
        "linkedin_message.docx": render_linkedin_message_docx(bundle.get("linkedin_message", {})),
        "elevator_pitch.docx": render_elevator_pitch_docx(bundle.get("elevator_pitch", {})),
        "interview_prep.docx": render_interview_prep_docx(bundle.get("interview_prep", {})),
        "gap_analysis.docx": render_gap_analysis_docx(bundle.get("gap_analysis", {})),
    }

    files: dict[str, bytes] = {}
    for filename, document in documents.items():
        buffer = io.BytesIO()
        document.save(buffer)
        files[filename] = buffer.getvalue()

    application = {
        "profile": profile,
        "job_analysis": job_analysis,
        "bundle": bundle,
        "fidelity": fidelity,
    }
    files["application.json"] = json.dumps(application, indent=2).encode("utf-8")

    return files


def write_to_folder(files: dict[str, bytes], output_dir: Path, company: str, role: str) -> Path:
    """Write a rendered bundle to <output_dir>/<company>-<role>/, overwriting."""
    folder = output_dir / job_folder_name(company, role)
    folder.mkdir(parents=True, exist_ok=True)
    for filename, data in files.items():
        (folder / filename).write_bytes(data)
    return folder


def build_zip(jobs: dict[str, dict[str, bytes]]) -> bytes:
    """Build one ZIP containing every job's folder of rendered files.

    `jobs` maps job_folder_name -> {filename: bytes}, as produced by
    render_all() per job.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder_name, files in jobs.items():
            for filename, data in files.items():
                zf.writestr(f"{folder_name}/{filename}", data)
    return buffer.getvalue()
