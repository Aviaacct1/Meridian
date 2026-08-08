"""Avia deck generator: the deck specification.

The spec carries content and structure only. No colours, no fonts, no geometry.
Three renderers read it:

    render_observatory.py   The Aviation Observatory / Meridian style, HTML and PDF
    render_avia.py          Avia Solutions house style, PowerPoint
    render_template.py      A client-supplied .pptx or .potx, populated

Splitting content from rendering is what makes the third one possible at all: a
client template gives us their layouts, and the renderer maps slide types onto them.

A deck is a dict:
    {"meta": {...}, "slides": [ {...}, ... ]}

Every slide carries: type, section (the eyebrow), title, subtitle, source, notes.
Type-specific keys are listed against each builder below.

Avia Solutions Limited. All rights reserved.
"""


def deck(codename, title, strap, prepared_for, event, date, status=None,
         confidentiality="Commercial in Confidence", currency_note=None,
         author="The Aviation Observatory"):
    """author: who publishes the file. Product decks go out under The Aviation
    Observatory, the separate company; set it to Avia Solutions for an Avia client
    deliverable built through the same renderers."""
    return {"meta": {"codename": codename, "title": title, "strap": strap,
                     "prepared_for": prepared_for, "event": event, "date": date,
                     "status": status, "confidentiality": confidentiality,
                     "currency_note": currency_note, "author": author},
            "slides": []}


def _s(kind, **kw):
    d = {"type": kind, "section": kw.pop("section", None),
         "title": kw.pop("title", None), "subtitle": kw.pop("subtitle", None),
         "source": kw.pop("source", None), "notes": kw.pop("notes", None)}
    d.update(kw)
    return d


# --- slide builders --------------------------------------------------------

def cover(title_lines, image=None, family="globe", **kw):
    """title_lines: list of str. The renderer decides the display treatment."""
    return _s("cover", title_lines=title_lines, image=image,
              family=family, **kw)


def contents(items, **kw):
    """items: list of (number, title, page). Page is filled on the second pass."""
    return _s("contents", items=items, **kw)


def divider(number, title, strap=None, image=None, family="field",
            prefer=None, **kw):
    """prefer: a library filename token this divider would rather have."""
    return _s("divider", number=number, strap=strap, image=image,
              title=title, family=family, prefer=prefer, **kw)


def stat_row(stats, table=None, callouts=None, figure=None, **kw):
    """stats: list of (label, value, accent_bool). The summary slide."""
    return _s("stat_row", stats=stats, table=table, callouts=callouts or [],
              figure=figure, **kw)


def keynumbers(items, **kw):
    """items: list of (value, statement)."""
    return _s("keynumbers", items=items, **kw)


def table(table, panels=None, callouts=None, figure=None, bullets=None, **kw):
    """table: {"head": [...], "rows": [[...]], "widths": [...], "aligns": [...],
               "total": bool}"""
    return _s("table", table=table, panels=panels or [],
              callouts=callouts or [], figure=figure, bullets=bullets or [], **kw)


def figure(image, panels=None, callouts=None, bullets=None, table=None, **kw):
    return _s("figure", image=image, panels=panels or [],
              callouts=callouts or [], bullets=bullets or [], table=table, **kw)


def prose(paras, panels=None, callouts=None, **kw):
    """paras: list of (heading_or_None, body)."""
    return _s("prose", paras=paras, panels=panels or [],
              callouts=callouts or [], **kw)


def grid(rows, accent_rows=None, callout=None, **kw):
    """rows: list of (heading, body). The 'choose X' and 'the case' slides."""
    return _s("grid", rows=rows, accent_rows=accent_rows or [],
              callout=callout, **kw)


def plate(slot, subject, credit, date, supports, subjects=None, body=None,
          panels=None, **kw):
    """An evidence plate: bespoke photography, body grid only.

    Observatory Brand Guidelines v1.3, chapter 14. A plate is an argument, not
    decoration: it supports a claim already made on the page, and the caption
    says which. Never full-bleed, never on a cover or divider, one to a page and
    four to a report.

    slot      the resolver key, e.g. "airport.aerial"
    subject   what the photograph shows, for caption line one
    credit    who supplied it, for caption line one and the rights record
    date      when it was taken, for caption line one
    supports  the claim it supports, for caption line two
    subjects  subject tags the resolver may match an upload or store image on
    """
    return _s("plate", slot=slot, subject=subject, credit=credit, date=date,
              supports=supports, subjects=subjects or [], body=body or [],
              panels=panels or [], image_kind="evidence", **kw)


def thanks(title, strap=None, image=None, family="globe", **kw):
    return _s("thanks", title=title, strap=strap, image=image,
              family=family, **kw)


# --- helpers ---------------------------------------------------------------

def panel(title, items, tone="neutral"):
    """tone: neutral | accent | caution. Renderers map tone to their palette."""
    return {"title": title, "items": items, "tone": tone}


def callout(lines, tone="accent"):
    return {"lines": lines if isinstance(lines, list) else [lines], "tone": tone}


def paginate(spec, cover_counts=False):
    """Assign page numbers and fill the contents slide from the section dividers.

    Returns the spec, mutated. Run once; the renderers read slide['page'].
    """
    page = 0
    sections = []
    for sl in spec["slides"]:
        if sl["type"] == "cover" and not cover_counts:
            sl["page"] = None
            continue
        page += 1
        sl["page"] = page
        if sl["type"] == "divider":
            sections.append((sl["number"], sl["title"], page))
    for sl in spec["slides"]:
        if sl["type"] == "contents" and sl.get("items"):
            filled = []
            by_title = {t: p for _, t, p in sections}
            for num, title, pg in sl["items"]:
                filled.append((num, title, by_title.get(title, pg)))
            sl["items"] = filled
    return spec


# --- content budget --------------------------------------------------------
# Slots that overflow are the main failure mode when the same spec is rendered
# into three different geometries. Budgets are characters, set from the slots
# that fit in the tightest of the three renderers.

BUDGET = {
    "title": 62, "subtitle": 104, "grid_head": 44, "grid_body": 250,
    "panel_item": 215, "callout_line": 58, "prose_head": 58, "prose_body": 430,
    "keynumber_value": 9, "keynumber_statement": 100, "table_cell": 58,
    "source": 430,
}


def check(spec, verbose=True):
    """Report every slot over budget. Run before rendering, in any renderer."""
    warn = []

    def w(i, what, text, key):
        if text and len(str(text)) > BUDGET[key]:
            warn.append("slide %d (%s): %s is %d chars, budget %d - %r"
                        % (i, spec["slides"][i - 1].get("title") or
                           spec["slides"][i - 1]["type"], what, len(str(text)),
                           BUDGET[key], str(text)[:60] + "..."))

    for i, sl in enumerate(spec["slides"], 1):
        w(i, "title", sl.get("title"), "title")
        w(i, "subtitle", sl.get("subtitle"), "subtitle")
        w(i, "source", sl.get("source"), "source")
        for h, b in sl.get("rows", []):
            w(i, "grid heading", h, "grid_head")
            w(i, "grid body", b, "grid_body")
        for h, b in sl.get("paras", []):
            w(i, "prose heading", h, "prose_head")
            w(i, "prose body", b, "prose_body")
        for v, st in sl.get("items", []) if sl["type"] == "keynumbers" else []:
            w(i, "key number", v, "keynumber_value")
            w(i, "key statement", st, "keynumber_statement")
        for p in sl.get("panels", []):
            for it in p["items"]:
                w(i, "panel item", it, "panel_item")
        for c in sl.get("callouts", []) + ([sl["callout"]] if sl.get("callout") else []):
            for line in c["lines"]:
                w(i, "callout line", line, "callout_line")
        t = sl.get("table")
        if t:
            for row in t["rows"]:
                for cell in row:
                    w(i, "table cell", cell, "table_cell")
    if verbose:
        if warn:
            print("CONTENT BUDGET: %d slot(s) over" % len(warn))
            for x in warn:
                print("  ", x)
        else:
            print("CONTENT BUDGET: clean")
    return warn
