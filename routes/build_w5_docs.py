"""Build the W5 Word deliverables from their markdown sources.

Run on the DevPC:  python routes\\build_w5_docs.py
Outputs, beside the sources in routes\\:
  Meridian-Standard-Terms-DRAFT.docx
  Meridian-Order-Form-TEMPLATE.docx
  Meridian-Launch-Customer-One-Pager-DRAFT.docx
  Meridian-Licence-Record-FORM.docx
  Meridian-Invoice-TEMPLATE.xlsx

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
    ("W5-STANDARD-TERMS.md",
     "Meridian-Standard-Terms-DRAFT.docx",
     "Meridian Standard Terms, draft v0.3",
     "DRAFT for legal review, not for issue to a client"),
    ("W5-ORDER-FORM.md",
     "Meridian-Order-Form-TEMPLATE.docx",
     "Meridian Order Form, template v0.3",
     "TEMPLATE, commercial in confidence"),
    ("W5-ONE-PAGER-19Sep2026.md",
     "Meridian-Launch-Customer-One-Pager-DRAFT.docx",
     "Meridian launch customer offer, draft v0.3",
     "DRAFT, commercial in confidence"),
    ("W5-LICENCE-RECORD.md",
     "Meridian-Licence-Record-FORM.docx",
     "Data licence position, record form v0.1",
     "Private and confidential, for completion by John Carter"),
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
            if any("-" in c for c in cells) and all(set(c) <= set("-: ") for c in cells):
                continue
            if not any(cells):
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
            width = max(len(r) for r in rows)
            rows = [r + [""] * (width - len(r)) for r in rows]
            table = doc.add_table(rows=len(rows), cols=width)
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
        problems += _core_author_problems(core)
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


# ------------------------------------------------------------------ the invoice
INVOICE_OUT = "Meridian-Invoice-TEMPLATE.xlsx"


def build_invoice(path=None):
    """The Aviation Observatory Limited invoice template. Figures are left blank on
    purpose: the amount comes from the client's Order Form, not from this file."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    path = Path(path or HERE / INVOICE_OUT)
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoice"

    head = Font(name="Arial", size=16, bold=True)
    bold = Font(name="Arial", size=10, bold=True)
    body = Font(name="Arial", size=10)
    note = Font(name="Arial", size=9, italic=True, color="595959")
    slot = Font(name="Arial", size=10, bold=True, color="8B0000")
    rule = Side(style="thin", color="BFBFBF")
    box = Border(left=rule, right=rule, top=rule, bottom=rule)
    shade = PatternFill("solid", fgColor="F2F2F2")

    for column, width in zip("ABCDE", (34, 16, 12, 14, 16)):
        ws.column_dimensions[column].width = width

    def put(cell, value, font=body, **kw):
        c = ws[cell]
        c.value = value
        c.font = font
        for key, val in kw.items():
            setattr(c, key, val)
        return c

    put("A1", "INVOICE", head)
    put("A2", "The Aviation Observatory Limited", bold)
    put("A3", "Company number 17411365")
    put("A4", "86-90 Paul Street, London EC2A 4NE")
    put("A5", "SLOT 1: VAT registration number, or the line stating TAO is not registered", slot)

    put("A7", "Invoice number", bold); put("B7", "")
    put("A8", "Invoice date", bold); put("B8", "")
    put("A9", "Payment due", bold); put("B9", "14 days from the invoice date")
    put("A10", "Order Form reference", bold); put("B10", "")
    put("A11", "Client purchase order", bold); put("B11", "")

    put("A13", "Billed to", bold)
    for row, label in zip(range(14, 19),
                          ("Client, registered name", "Registered number",
                           "Address", "Contact for payment", "Contact email")):
        put(f"A{row}", label); put(f"B{row}", "")

    put("A20", "Description", bold, fill=shade, border=box)
    put("B20", "Period", bold, fill=shade, border=box)
    put("C20", "Quantity", bold, fill=shade, border=box)
    put("D20", "Unit, £", bold, fill=shade, border=box)
    put("E20", "Amount, £", bold, fill=shade, border=box)
    for row in range(21, 27):
        for column in "ABCDE":
            cell = put(f"{column}{row}", "")
            cell.border = box
        ws[f"E{row}"].number_format = "#,##0.00"
    put("A21", "Meridian licence, band and Covered Airports per the Order Form")

    put("D28", "Net", bold); put("E28", "=SUM(E21:E26)").number_format = "#,##0.00"
    put("D29", "VAT", bold); put("E29", "").number_format = "#,##0.00"
    put("D30", "Total due", bold); put("E30", "=E28+E29", bold).number_format = "#,##0.00"

    put("A32", "Payment", bold)
    put("A33", "Annual in advance, invoiced on signature, payable within 14 days. "
               "All amounts are exclusive of VAT and in sterling.")
    put("A34", "Where the Order Form states quarterly payment, the licence remains annual and "
               "the whole year is owed from signature.")
    put("A36", "SLOT 7: bank details for The Aviation Observatory Limited. The account is not "
               "yet open and is opened before the first invoice is issued.", slot)
    for row in (37, 38, 39, 40):
        put(f"A{row}", ("Account name", "Sort code", "Account number",
                        "Reference to quote")[row - 37], bold)
        put(f"B{row}", "")

    put("A42", "Overdue invoices: TAO may suspend access where an undisputed invoice is unpaid "
               "10 days after written notice. Standard Terms, clause 10.", note)
    put("A43", "Prepared from PRICING-DECISION-2026.md v1.0. The amount comes from the client's "
               "Order Form.", note)

    ws["A5"].alignment = Alignment(wrap_text=False)
    wb.properties.creator = AUTHOR
    wb.properties.lastModifiedBy = AUTHOR
    wb.properties.title = "Meridian invoice template"
    wb.properties.category = "Meridian, World Routes 2026"
    wb.save(path)
    return path


def _core_author_problems(core):
    """Both writers emit the namespace inline on the tag, so match the tag, not a string."""
    problems = []
    creator = re.search(r"<dc:creator[^>]*>(.*?)</dc:creator>", core, re.S)
    modified = re.search(r"<cp:lastModifiedBy[^>]*>(.*?)</cp:lastModifiedBy>", core, re.S)
    if not creator or creator.group(1).strip() != AUTHOR:
        problems.append("author is not Avia Solutions")
    if not modified or modified.group(1).strip() != AUTHOR:
        problems.append("last-modified-by is not Avia Solutions")
    return problems


def verify_xlsx(path):
    problems = []
    with zipfile.ZipFile(path) as z:
        core = z.read("docProps/core.xml").decode("utf-8")
        problems += _core_author_problems(core)
        for name in z.namelist():
            if not name.endswith(".xml"):
                continue
            xml = z.read(name).decode("utf-8", "ignore")
            for dash in ("\u2014", "\u2013"):
                if dash in xml:
                    problems.append(f"{name}: an em or en dash reached the file")
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
    path = build_invoice()
    problems = verify_xlsx(path)
    print(f"{INVOICE_OUT}: {'VERIFIED' if not problems else 'FAILED'}")
    for problem in problems:
        print(f"   {problem}")
        failed = True
    sys.exit(1 if failed else 0)
