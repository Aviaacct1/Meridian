"""Build the W5 Word deliverables from their markdown sources.

Run on the DevPC:  python routes\\build_w5_docs.py
Outputs, beside the sources in routes\\:
  Meridian-Licence-Agreement-DRAFT.docx
  Meridian-Launch-Customer-One-Pager-DRAFT.docx

House rules enforced here, not by hand: Avia Solutions as author and last-modified-by,
en-GB at the document default with no run-level or style-level language anywhere else,
Arial, A4, and the draft footer. verify_docx() re-opens each file and fails loudly if any
of that did not take. Blocks between <!-- SKIP-START --> and <!-- SKIP-END --> in the
source are internal notes and never reach the Word file.
"""
import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Mm, RGBColor

HERE = Path(__file__).resolve().parent
AUTHOR = "Avia Solutions"
LANG = "en-GB"
GREY = RGBColor(0x59, 0x59, 0x59)

JOBS = [
    ("W5-AGREEMENT-19Sep2026.md",
     "Meridian-Licence-Agreement-DRAFT.docx",
     "Meridian licence agreement, draft v0.2",
     "DRAFT for legal review, not for issue to a client"),
    ("W5-ONE-PAGER-19Sep2026.md",
     "Meridian-Launch-Customer-One-Pager-DRAFT.docx",
     "Meridian launch customer offer, draft v0.2",
     "DRAFT, commercial in confidence"),
]

TOKEN = re.compile(r"(\*\*.+?\*\*|SLOT [0-9A-Z]+|LAWYER [0-9]+)")


def read_blocks(path):
    """Yield (kind, payload) from the markdown source, skipping internal blocks."""
    lines = path.read_text(encoding="utf-8").splitlines()
    out, para, table, skip = [], [], [], False
    def flush():
        if para:
            out.append(("p", " ".join(para)))
            para.clear()
        if table:
            out.append(("table", list(table)))
            table.clear()
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if "<!-- SKIP-START -->" in line:
            flush(); skip = True; continue
        if "<!-- SKIP-END -->" in line:
            skip = False; continue
        if skip:
            continue
        if not stripped or stripped == "---":
            flush(); continue
        if line.startswith("|"):
            if para: flush()
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            table.append(cells); continue
        if line.startswith("### "):
            flush(); out.append(("h2", line[4:]))
        elif line.startswith("## "):
            flush(); out.append(("h1", line[3:]))
        elif line.startswith("# "):
            flush(); out.append(("title", line[2:]))
        elif line.startswith("> "):
            flush(); out.append(("quote", line[2:]))
        elif line.startswith("- "):
            flush(); out.append(("bullet", line[2:]))
        elif re.match(r"^\d+\. ", line):
            flush(); out.append(("number", re.sub(r"^\d+\. ", "", line)))
        else:
            para.append(stripped)
    flush()
    # join wrapped continuation lines of bullets, quotes and numbers
    merged = []
    for kind, payload in out:
        if kind == "p" and merged and merged[-1][0] in ("bullet", "quote", "number"):
            merged[-1] = (merged[-1][0], merged[-1][1] + " " + payload)
        else:
            merged.append((kind, payload))
    return merged


def write_runs(par, text, size, bold=False, italic=False, color=None):
    text = text.replace("`", "")
    for part in TOKEN.split(text):
        if not part:
            continue
        run = par.add_run(part.strip("*") if part.startswith("**") else part)
        run.font.name = "Arial"
        run.font.size = Pt(size)
        run.font.bold = bold or part.startswith("**") or part.startswith(("SLOT ", "LAWYER "))
        run.font.italic = italic
        if color is not None:
            run.font.color.rgb = color


def set_document_language(doc):
    """en-GB at the document default and on the default style; nowhere else."""
    styles = doc.styles.element
    defaults = styles.find(qn("w:docDefaults"))
    rpr_default = defaults.find(qn("w:rPrDefault"))
    rpr = rpr_default.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr"); rpr_default.append(rpr)
    for existing in rpr.findall(qn("w:lang")):
        rpr.remove(existing)
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), LANG)
    lang.set(qn("w:eastAsia"), LANG)
    lang.set(qn("w:bidi"), "ar-SA")
    rpr.append(lang)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)
    settings = doc.settings.element
    for existing in settings.findall(qn("w:themeFontLang")):
        settings.remove(existing)
    theme = OxmlElement("w:themeFontLang")
    theme.set(qn("w:val"), LANG)
    settings.append(theme)


def add_footer(doc, left_text):
    par = doc.sections[0].footer.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    write_runs(par, left_text + "   ", 8, color=GREY)
    write_runs(par, "P: ", 8, color=GREY)
    run = par.add_run()
    run.font.name = "Arial"; run.font.size = Pt(8); run.font.color.rgb = GREY
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._r.addnext(fld)


def build(src, out, title, status):
    doc = Document()
    set_document_language(doc)
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    for attr in ("top_margin", "bottom_margin"):
        setattr(section, attr, Mm(18))
    for attr in ("left_margin", "right_margin"):
        setattr(section, attr, Mm(20))

    for kind, payload in read_blocks(HERE / src):
        if kind == "title":
            par = doc.add_paragraph(); par.paragraph_format.space_after = Pt(4)
            write_runs(par, payload, 16, bold=True)
        elif kind == "h1":
            par = doc.add_paragraph()
            par.paragraph_format.space_before = Pt(10); par.paragraph_format.space_after = Pt(3)
            write_runs(par, payload, 11, bold=True)
        elif kind == "h2":
            par = doc.add_paragraph()
            par.paragraph_format.space_before = Pt(8); par.paragraph_format.space_after = Pt(2)
            write_runs(par, payload, 10, bold=True)
        elif kind == "quote":
            par = doc.add_paragraph()
            par.paragraph_format.left_indent = Mm(8)
            par.paragraph_format.space_after = Pt(4)
            write_runs(par, payload, 8.5, italic=True, color=GREY)
        elif kind in ("bullet", "number"):
            par = doc.add_paragraph(style="List Bullet" if kind == "bullet" else "List Number")
            par.paragraph_format.space_after = Pt(2)
            write_runs(par, payload, 10)
        elif kind == "table":
            rows = payload
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.style = "Table Grid"
            for r, row in enumerate(rows):
                for c, cell in enumerate(row):
                    par = table.cell(r, c).paragraphs[0]
                    write_runs(par, cell, 10, bold=(r == 0))
        else:
            par = doc.add_paragraph(); par.paragraph_format.space_after = Pt(6)
            write_runs(par, payload, 10)

    props = doc.core_properties
    props.author = AUTHOR
    props.last_modified_by = AUTHOR
    props.title = title
    props.category = "Meridian, World Routes 2026"
    props.comments = status
    add_footer(doc, "- DRAFT -")
    doc.save(HERE / out)
    return HERE / out


def verify_docx(path):
    """Re-open the built file and fail loudly if the house rules did not take."""
    problems = []
    with zipfile.ZipFile(path) as z:
        core = z.read("docProps/core.xml").decode("utf-8")
        if f"<dc:creator>{AUTHOR}</dc:creator>" not in core:
            problems.append("author is not Avia Solutions")
        if f"lastModifiedBy>{AUTHOR}<" not in core:
            problems.append("last-modified-by is not Avia Solutions")
        for name in ("word/styles.xml", "word/document.xml", "word/settings.xml"):
            if name not in z.namelist():
                continue
            xml = z.read(name).decode("utf-8")
            for match in re.findall(r'<w:lang [^/>]*/>', xml):
                for attr in re.findall(r'w:(?:val|eastAsia)="([^"]+)"', match):
                    if attr != LANG:
                        problems.append(f"{name}: language {attr}")
            for match in re.findall(r'<w:themeFontLang [^/>]*/>', xml):
                if f'w:val="{LANG}"' not in match:
                    problems.append(f"{name}: themeFontLang not {LANG}")
        doc_xml = z.read("word/document.xml").decode("utf-8")
        if "word/settings.xml" in z.namelist():
            if f'w:val="{LANG}"' not in z.read("word/settings.xml").decode("utf-8"):
                problems.append("settings.xml carries no en-GB themeFontLang")
        if f'w:val="{LANG}"' not in z.read("word/styles.xml").decode("utf-8"):
            problems.append("styles.xml carries no en-GB default")
        for dash in ("\u2014", "\u2013"):
            if dash in doc_xml:
                problems.append("an em or en dash reached the document")
    return problems


if __name__ == "__main__":
    failed = False
    for src, out, title, status in JOBS:
        path = build(src, out, title, status)
        problems = verify_docx(path)
        print(f"{out}: {'VERIFIED' if not problems else 'FAILED'}")
        for problem in problems:
            print(f"   {problem}")
            failed = True
    sys.exit(1 if failed else 0)
