"""Shared DOCX styling primitives for render.py's seven document builders.

Single column, standard heading styles, no tables or text boxes, system
fonts — the kind of resume an applicant-tracking system can actually parse.
Colour, bold weight, size, and tab-aligned dates are all safe to lean on for
visual polish: they only change how text looks, never how it flows, so they
never risk an ATS parser losing or reordering content the way a table,
text box, or multi-column layout can.
"""

from __future__ import annotations

import docx
from docx.enum.text import WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

BODY_FONT = "Calibri"
BODY_SIZE = Pt(11)

# Same warm terracotta brand used in the web app (resume_match/ui.py), so a
# downloaded document and the app it came from feel like one product.
ACCENT_COLOR = RGBColor(0xC1, 0x66, 0x2E)
TEXT_COLOR = RGBColor(0x2B, 0x24, 0x20)
MUTED_COLOR = RGBColor(0x8A, 0x75, 0x66)
BORDER_COLOR_HEX = "EADFD0"
ACCENT_COLOR_HEX = "C1662E"


def _apply_bottom_border(p_pr, val: str, size: int, color: str) -> None:
    for existing in p_pr.findall(qn("w:pBdr")):
        p_pr.remove(existing)
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), val)
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4" if val == "single" else "0")
    bottom.set(qn("w:color"), color)
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


def add_bottom_border(paragraph, color_hex: str, size: int = 6) -> None:
    """A thin horizontal rule under a paragraph — plain OOXML paragraph
    borders, not a drawn shape or text box, so it reads as ordinary
    formatting to any parser, the same way bold or a font color does."""
    _apply_bottom_border(paragraph._p.get_or_add_pPr(), "single", size, color_hex)


def _clear_style_border(style) -> None:
    """Word's built-in "Title" style ships with its own bottom border baked
    into python-docx's default template; turn it off so the only borders
    visible are the ones this module explicitly adds."""
    _apply_bottom_border(style.element.get_or_add_pPr(), "none", 0, "auto")


def _style_heading(style, size: Pt, color: RGBColor, small_caps: bool = False) -> None:
    style.font.name = BODY_FONT
    style.font.size = size
    style.font.bold = True
    style.font.color.rgb = color
    style.font.small_caps = small_caps


def new_document() -> docx.Document:
    document = docx.Document()

    normal = document.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = BODY_SIZE
    normal.font.color.rgb = TEXT_COLOR

    _style_heading(document.styles["Title"], Pt(26), ACCENT_COLOR)
    _clear_style_border(document.styles["Title"])
    _style_heading(document.styles["Heading 1"], Pt(13), ACCENT_COLOR, small_caps=True)
    _style_heading(document.styles["Heading 2"], Pt(11.5), TEXT_COLOR)

    bullet = document.styles["List Bullet"]
    bullet.font.name = BODY_FONT
    bullet.font.size = BODY_SIZE
    bullet.paragraph_format.space_after = Pt(2)

    for section in document.sections:
        section.left_margin = section.right_margin = Inches(1)
    return document


def usable_width(document: docx.Document) -> Inches:
    section = document.sections[0]
    return section.page_width - section.left_margin - section.right_margin


# (size, color, small_caps) per heading level — applied to each run directly,
# not just left to the style definition. Real Microsoft Word resolves a
# paragraph's style-level formatting correctly, but other DOCX renderers
# (Google Docs, LibreOffice, Apple Pages, various online viewers) are known to
# be inconsistent about honoring custom style definitions written by
# python-docx, and can silently fall back to plain black text. Setting the
# same formatting on the run itself is unambiguous in every renderer.
_HEADING_RUN_STYLE = {
    0: (Pt(26), ACCENT_COLOR, False),
    1: (Pt(13), ACCENT_COLOR, True),
    2: (Pt(11.5), TEXT_COLOR, False),
}


def add_heading(document: docx.Document, text: str, level: int = 1):
    heading = document.add_heading(text, level=level)
    size, color, small_caps = _HEADING_RUN_STYLE.get(level, (BODY_SIZE, TEXT_COLOR, False))
    for run in heading.runs:
        run.font.name = BODY_FONT
        run.font.size = size
        run.font.color.rgb = color
        run.font.bold = True
        run.font.small_caps = small_caps
    if level == 1:
        heading.paragraph_format.space_before = Pt(14)
        heading.paragraph_format.space_after = Pt(4)
        add_bottom_border(heading, ACCENT_COLOR_HEX)
    return heading


def add_dated_heading(document: docx.Document, title: str, dates: str) -> None:
    """A bold title on the left, dates right-aligned on the same line via a
    tab stop — real Word tab-stop alignment, not a table, so it still reads
    as one line of plain text to any parser."""
    para = document.add_paragraph()
    if dates:
        para.paragraph_format.tab_stops.add_tab_stop(usable_width(document), WD_TAB_ALIGNMENT.RIGHT)
    para.add_run(title).bold = True
    if dates:
        date_run = para.add_run(f"\t{dates}")
        date_run.italic = True
        date_run.font.color.rgb = MUTED_COLOR
    return para


def _names_match(a: str, b: str) -> bool:
    """True if `a` and `b` look like the same skill, allowing one side to
    carry a qualifier suffix the other doesn't (e.g. "React" vs. "React
    (familiar with)") without doing a loose substring match that could cross
    word boundaries (e.g. "SQL" must not match "PostgreSQL")."""
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if not shorter or not longer.startswith(shorter):
        return False
    return longer[len(shorter) : len(shorter) + 1] in (" ", "(")


def group_skills(skill_names: list[str], categories: dict[str, str]) -> list[tuple[str, list[str]]]:
    """Group flat skill names by category, using the credential profile's own
    category tags (set during profiling, not guessed at render time)."""
    groups: dict[str, list[str]] = {}
    uncategorized = []
    for name in skill_names:
        lowered = name.strip().lower()
        category = categories.get(lowered)
        if not category:
            category = next((cat for known, cat in categories.items() if _names_match(known, lowered)), None)
        if category:
            groups.setdefault(category, []).append(name)
        else:
            uncategorized.append(name)
    ordered = list(groups.items())
    if uncategorized:
        ordered.append(("Other", uncategorized))
    return ordered


def skill_categories(profile: dict) -> dict[str, str]:
    """name.lower() -> category, from the credential profile's skills list."""
    lookup = {}
    for skill in profile.get("skills", []):
        name, category = skill.get("name", "").strip(), skill.get("category", "").strip()
        if name and category:
            lookup[name.lower()] = category
    return lookup
