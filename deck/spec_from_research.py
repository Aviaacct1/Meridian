#!/usr/bin/env python3
"""Turn research output into a deck spec.

This is the connector that was missing. The two halves already existed:

  app/market_research_module.py    the relevance engine, which blocks matter
  app/market_research_executor.py  the typed research output, findings + citations
  v4/deck_spec.py                  the renderer-agnostic content spec
  v4/render_pptx.py                the Observatory PowerPoint renderer

The old path, app/city_pair_pptx_generator.py, took the same research and put
`findings[:5]` on an unstyled slide as bullets. This maps the same input onto
the spec instead, so it renders in house style with resolved imagery.

What it does NOT do, and should not pretend to: write. Five bullets of claim
plus value is evidence, not an argument. The block's own `summary` and
`presentation_text` fields carry the prose, and where a research run leaves
them empty the section will read thin. That gap closes with a writing pass over
the findings, not here.

Input shapes accepted, in order of preference:
  1. a ResearchOutput object from market_research_executor
  2. its JSON, via generate_json_output
  3. the loose dict the old generator took:
     {block_id: {"findings": [...], "summary": str}}

Avia Solutions Limited. All rights reserved.
"""

import json
import re

import deck_spec as S

# Section order and display names. Follows the Avia deck spine: set the market
# up, prove the demand, prove the airport, then the numbers.
BLOCK_ORDER = [
    ("economic_context",     "The market"),
    ("corporate_links",      "Corporate and sector links"),
    ("trade",                "Trade and investment"),
    ("tourism",              "Visitor demand"),
    ("diaspora",             "Diaspora and visiting friends and relatives"),
    ("education",            "Education links"),
    ("passenger_profile",    "Who travels today"),
    ("airport_overview",     "The airport"),
    ("non_cannibalization",  "Why this does not cannibalise"),
    ("case_study",           "Precedent"),
]

# Which library family dresses each section divider.
BLOCK_FAMILY = {
    "economic_context": "globe", "corporate_links": "instruments",
    "trade": "globe", "tourism": "field", "diaspora": "field",
    "education": "instruments", "passenger_profile": "instruments",
    "airport_overview": "operations", "non_cannibalization": "instruments",
    "case_study": "field",
}

SOURCE_FALLBACK = ("Source: OAG schedules, Sabre MIDT, AviaSolutions analysis (Avia Cortex).")

# Which end of the route each section is actually about. A divider for visitor
# demand wants the destination; one for the airport wants the origin. Passing
# both everywhere would let the resolver put Austin on the Edinburgh airport page.
_SUBJECT_END = {
    "economic_context": "both", "corporate_links": "both", "trade": "both",
    "tourism": "dest", "diaspora": "origin", "education": "both",
    "passenger_profile": "origin", "airport_overview": "origin",
    "non_cannibalization": "origin", "case_study": "both",
}


# Which figure belongs to which section, and in what order. A chart goes where
# it carries that section's argument, not wherever there is room:
#
#   the airport            what it carries and how that has moved, then where
#                          its capacity goes
#   who travels today      how full the aircraft leave, which is the one number
#                          an airline reads before anything else
#   why not cannibalise    who already flies from here and at what scale
#   visitor demand         the far end's own traffic
#
# A section with no figure is unchanged. Nothing here draws a placeholder.
BLOCK_FIGURES = {
    "airport_overview": ["airport_pax", "airport_haul"],
    "passenger_profile": ["airport_load"],
    "non_cannibalization": ["airport_airlines"],
    "tourism": ["dest_pax"],
}

# Each figure's own caption. The chart states its unit and period on itself, so
# these say what the reader should take from it and nothing the chart repeats.
FIGURE_TITLE = {
    "airport_pax": "What the airport carries",
    "airport_haul": "Where its capacity goes",
    "airport_airlines": "Who flies from here today",
    "airport_load": "How full the aircraft leave",
    "dest_pax": "The far end",
}


def _subjects(bid, origin, dest):
    """Subject tags for a divider, most specific first.

    WITHOUT THESE THE RESOLVER CAN ONLY REACH THE GENERIC LIBRARY. Its order is
    the user's own upload, then the user's upload by subject, then the licensed
    subject store, then a brand-library frame by family. Tiers two and three are
    keyed on subject tags, and the dividers were passing none, so every deck fell
    through to a stock globe or a runway however much Edinburgh photography the
    store held. That is John's "no photos of the airport", 7 August, and it was a
    missing argument rather than a missing capability.
    """
    end = _SUBJECT_END.get(bid, "both")
    tags = []
    if end in ("origin", "both") and origin:
        tags += ["%s airport" % origin, origin]
    if end in ("dest", "both") and dest:
        tags += ["%s airport" % dest, dest]
    return [t for t in tags if t]

MAX_KEYNUMBERS = 6          # per slide, before it stops being readable
MAX_GRID_ROWS = 6
DROP = ("optional", "skip")  # relevance values that do not earn a section


# ---------------------------------------------------------------------------
# Reading whatever we were handed
# ---------------------------------------------------------------------------
def _as_dict(obj):
    """ResearchOutput, its JSON, or the loose dict. Returns a common shape."""
    if isinstance(obj, str):
        obj = json.loads(obj)
    if hasattr(obj, "blocks"):                      # a ResearchOutput
        return {
            "route": getattr(obj, "route", ""),
            "airline": getattr(obj, "airline", ""),
            "origin_city": getattr(obj, "origin_city", ""),
            "destination_city": getattr(obj, "destination_city", ""),
            "executive_summary": getattr(obj, "executive_summary", ""),
            "key_statistics": dict(getattr(obj, "key_statistics", {}) or {}),
            "blocks": [_block_as_dict(b) for b in obj.blocks],
        }
    if isinstance(obj, dict) and "blocks" in obj:   # already the JSON form
        out = dict(obj)
        out["blocks"] = [_block_as_dict(b) for b in obj["blocks"]]
        return out
    # the loose {block_id: {...}} form the old generator took
    blocks = []
    for bid, body in (obj or {}).items():
        blocks.append(_block_as_dict(dict(body or {}, block_id=bid)))
    return {"blocks": blocks}


def _block_as_dict(b):
    g = (lambda k, d=None: b.get(k, d)) if isinstance(b, dict) \
        else (lambda k, d=None: getattr(b, k, d))
    return {
        "block_id": g("block_id", "") or "",
        "block_name": g("block_name", "") or "",
        "relevance": str(g("relevance", "include") or "include").lower(),
        "summary": g("summary", "") or "",
        "presentation_text": g("presentation_text", "") or "",
        "data_gaps": list(g("data_gaps", []) or []),
        "findings": [_finding_as_dict(f) for f in (g("findings", []) or [])],
    }


def _finding_as_dict(f):
    """Normalise a finding from either shape.

    Two shapes exist in the codebase and they are NOT the same:

    market_research_executor.Finding  claim, value, unit, year, citations[],
                                      relevance_to_case, is_single_source
    research_provider.research_block  claim, value, unit, year, source_name, url

    The provider's is flatter: one source per finding, inline, and no
    relevance_to_case. Reading only the first shape produced slides with no
    attribution line at all, silently, because `citations` was simply absent.
    """
    g = (lambda k, d=None: f.get(k, d)) if isinstance(f, dict) \
        else (lambda k, d=None: getattr(f, k, d))
    cites = [_cite_as_dict(c) for c in (g("citations", []) or [])]
    if not cites and (g("source_name") or g("url")):
        cites = [{"source_name": (g("source_name") or "").strip(),
                  "title": (g("source_title") or "").strip(),
                  "date": (str(g("source_date") or g("year") or "")).strip(),
                  "url": (g("url") or "").strip()}]
    return {
        "claim": (g("claim", "") or "").strip(),
        "caption": (g("caption", "") or "").strip(),
        "value": (str(g("value", "") or "")).strip(),
        "unit": (g("unit", "") or "").strip(),
        "year": (str(g("year", "") or "")).strip(),
        "relevance_to_case": (g("relevance_to_case", "") or "").strip(),
        # a lone inline source IS a single source, whether or not it says so
        "is_single_source": bool(g("is_single_source", len(cites) < 2)),
        "citations": cites,
    }


def _cite_as_dict(c):
    g = (lambda k, d="": c.get(k, d)) if isinstance(c, dict) \
        else (lambda k, d="": getattr(c, k, d))
    return {"source_name": g("source_name") or "", "title": g("title") or "",
            "date": g("date") or "", "url": g("url") or ""}


# ---------------------------------------------------------------------------
# Shaping
# ---------------------------------------------------------------------------
def _sources_line(findings, prefix="Source: ", limit=None):
    """One attribution line per slide, deduplicated, in first-seen order.

    `limit` caps the list where a slide draws on many sections at once, as the
    closing "why this route" page does. The line has a character budget, and a
    truncated list that fits beats a complete one that overprints the page.
    """
    seen, parts = set(), []
    for f in findings:
        for c in f["citations"]:
            name = c["source_name"] or c["title"]
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            parts.append("%s%s" % (name, ", %s" % c["date"] if c["date"] else ""))
    if not parts:
        return None
    if limit and len(parts) > limit:
        parts = parts[:limit] + ["and %d more, cited in full in each section"
                                 % (len(parts) - limit)]
    return prefix + "; ".join(parts)


# A claim often opens with an adverbial: "In its Tech in the UK 2024 report,",
# "According to Scotland's Census 2022,", "As of 2024,". Taking the first clause
# blindly makes that fragment the row heading, which reads as an unfinished
# sentence above the same sentence written out in full.
_ADVERBIAL = re.compile(
    r"^(in|on|at|by|as of|according to|between|since|during|under|following|"
    r"despite|from|after|over|throughout|across)\b[^,]{0,70},\s*", re.I)


# The ellipsis costs three characters, so the cut is made three inside the slot.
HEAD_LIMIT = S.BUDGET["grid_head"] - 3


def _head(claim, limit=HEAD_LIMIT):
    """A short head for a grid cell: the first clause of the claim.

    The claim's own opening adverbial is skipped, not used. It carries the
    source or the date, which the slide's attribution line already states.
    """
    claim = re.sub(r"\s+", " ", claim).strip()
    body = _ADVERBIAL.sub("", claim).strip()
    if body:
        claim = body[0].upper() + body[1:]
    m = re.split(r",| which | that | and | with ", claim, maxsplit=1)
    head = (m[0] if m else claim).strip(" .")
    if len(head) > limit:
        head = head[:limit].rsplit(" ", 1)[0] + "..."
    return head or claim[:limit]


def _clause(text, limit=None):
    """A line trimmed to a boundary rather than mid-sentence or mid-word.

    The callout used to be built by lowercasing the first clause of the claim and
    cutting it at a character count, which produced "$268.4B, austin's metropolitan
    economy produced..." : a proper noun in lower case, cut mid-sentence, with the
    figure repeated inside its own callout.
    """
    limit = limit or (S.BUDGET["callout_line"] - 14)
    text = _ADVERBIAL.sub("", re.sub(r"\s+", " ", text or "").strip())
    if text:
        text = text[0].upper() + text[1:]
    if len(text) <= limit:
        return text.rstrip(" .")
    cut = text[:limit]
    for sep in (". ", ", ", "; "):
        i = cut.rfind(sep)
        if i > limit * 0.45:
            return cut[:i].rstrip(" .,;")
    # No clause break inside the budget: cut on a word and then drop any trailing
    # function word, so the line does not end "Texas and the." or "University of."
    words = cut.rsplit(" ", 1)[0].split()
    DANGLING = {"and", "the", "of", "a", "an", "to", "for", "in", "on", "at", "with",
                "by", "from", "its", "is", "as", "that", "which", "into", "over",
                "than", "their", "his", "her", "or", "but", "per", "up"}
    while words and words[-1].lower().strip(",;") in DANGLING:
        words.pop()
    return " ".join(words).rstrip(" .,;")


def _sentence(s):
    """One properly punctuated sentence."""
    s = re.sub(r"\s+", " ", (s or "").strip())
    if s and s[-1] not in ".?!":
        s += "."
    return s


def _statement(f):
    """The sentence beside a big number. The unit lives HERE, not in the value.

    A keynumbers value must stay short enough to set at 36pt in a 300px
    column. Folding the unit into it produced "$4.5bn Massachusetts goods
    exports to the UK" as the display number, which wrapped to four lines and
    overprinted the row beneath.
    """
    # The caption is written for this slot: it completes the number rather than
    # restating it. The hand-written Liguria deck runs 61 to 88 characters here,
    # against a budget of 100. The first live run, which had no caption and fell
    # back to the claim, ran 169 to 284 and repeated the figure inside the
    # sentence, so the eye read the number twice and the block set small.
    if f.get("caption"):
        return _sentence(f["caption"])
    # The unit is not repeated: the claim carries it in words, and appending
    # "(employees, 2024)" to a full sentence reads like a database dump. Only
    # the year is added, and only where the claim does not already state it.
    parts = [_sentence(f["claim"])]
    # Only append the year if the claim names NO year at all. Appending it when
    # the claim already dates something else produced "fell 1.7% in 2024, 2025".
    if f["year"] and not re.search(r"\b(19|20)\d{2}\b", f["claim"]):
        parts[0] = _sentence("%s, %s" % (f["claim"].rstrip("."), f["year"]))
    if f["relevance_to_case"]:
        parts.append(_sentence(f["relevance_to_case"]))
    return " ".join(parts)


# Beyond this a value is a phrase, not a display number, and belongs in a grid
# row. Tied to the spec's own budget so the two cannot drift: at 12 the live run
# set "$1,024.6bn" as a headline figure, three characters over what the slot holds.
MAX_VALUE_CHARS = S.BUDGET["keynumber_value"]


def _value_label(f):
    """The display number, bare. No unit, no qualifier."""
    return re.sub(r"\s+", " ", f["value"]).strip()


def _is_display_number(f):
    """Short enough to set large. Long values are evidence, not headlines."""
    v = _value_label(f)
    return bool(v) and len(v) <= MAX_VALUE_CHARS


def _chunk(items, n):
    return [items[i:i + n] for i in range(0, len(items), n)] or [[]]


def _lead_prose(block):
    """The paragraph that opens a section. presentation_text beats summary.

    research_provider returns findings only, with neither field, so a section
    built straight from a live provider run has NO opening paragraph and reads
    as evidence without an argument. That is the honest state, not a bug to
    paper over: the writing pass fills these two fields.
    """
    return (block["presentation_text"] or block["summary"] or "").strip()


def missing_prose(research):
    """Blocks with findings but no prose. Print this after any live run."""
    r = _as_dict(research)
    return [b["block_name"] or b["block_id"] for b in r["blocks"]
            if b["findings"] and not _lead_prose(b)]


# ---------------------------------------------------------------------------
# The methodology paragraphs. Descriptive, and deliberately carrying no figure: a
# number here would be a claim about a particular route, and this slide is the same
# in every deck. Written from what the engine does, not from a brochure.
METHODOLOGY = [
    ("Where the demand comes from",
     "The market is measured, not assumed. Point of origin traffic from the Sabre "
     "booking data gives the true size of the origin and destination market in the "
     "catchment, city by city, rather than counting what happens to fly through the "
     "airport today. The catchment is drawn on drive time and population, and every "
     "airport a traveller could reasonably choose is included, so a market shared "
     "with a larger neighbour is treated as shared."),
    ("How much of it a nonstop wins",
     "Share is set by a quality of service index. Each airport and routing competing "
     "for the same traveller is scored on journey time, frequency and connection "
     "quality, and the nonstop takes the share that score implies. Where measured "
     "catchment truth exists for an airport, from survey or mobility data, it "
     "overrides the modelled share."),
    ("What the airline adds on top",
     "Connecting traffic is built separately from the local market: the feed behind "
     "the origin and the flow beyond the destination, each scored for whether the "
     "connection is online, within the alliance or interline, and filtered for "
     "circuity and minimum connecting time. The forecast is then flown: capacity, "
     "planned load factor and spill decide what the aircraft actually carries."),
    ("Why the numbers can be tested",
     "The engine is calibrated against launched route outturn. Every forecast is "
     "graded against the first full year the route actually flew, so the method has "
     "a published record rather than an assertion of accuracy, reported against the "
     "launches it has been tested on rather than asserted. The record for this "
     "airport is available on request."),
]


def _why_rows(chosen, forecast_line, limit=5):
    """The case in one page: the strongest sourced fact from each section.

    Drawn from the findings rather than written, so every line on it is already
    attributed. The forecast leads where there is one.
    """
    rows, sources = [], []
    if forecast_line:
        rows.append(("The forecast", _sentence(forecast_line)))
    for _bid, name, b in chosen:
        numeric = [f for f in b["findings"] if _is_display_number(f)]
        pick = (numeric or b["findings"])[:1]
        if not pick:
            continue
        f = pick[0]
        rows.append((name, _statement(f)))
        sources.extend(f["citations"])
    return rows[:limit], (_sources_line([{"citations": sources}], limit=3)
                          if sources else None)


def build_spec(research, forecast=None, *, codename, title, strap, prepared_for,
               event="", date="", confidentiality="Commercial in Confidence",
               include_optional=False, max_sections=8, assumptions=None,
               forecast_line="", author="The Aviation Observatory",
               figures=None, route_facts=None, fig_sources=None):
    """Assemble a deck spec.

    forecast     the dict from forecast_spec, or None for a research-only deck
    assumptions  list of (label, value) for the key assumptions slide
    author       who publishes the file; product decks go out under the Observatory
    figures      {slot: png path} from deck_figures.build. A slot that is absent
                 loses its slide; nothing here draws a placeholder, because a
                 grey box captioned "figure not generated" on a sales deck is
                 worse than a deck with one page fewer
    route_facts  the lines under the route map, from deck_figures.route_facts
    fig_sources  {slot: source line} from deck_figures.build_airport. The chart
                 leaves its attribution off the PNG so the slide can carry it in
                 house typography, which is what the build audit checks
    """
    publisher = author
    r = _as_dict(research)
    origin = r.get("origin_city") or ""
    dest = r.get("destination_city") or ""

    spec = S.deck(codename=codename, title=title, strap=strap,
                  prepared_for=prepared_for, event=event, date=date,
                  confidentiality=confidentiality, author=publisher)
    add = spec["slides"].append

    add(S.cover(title_lines=[l for l in title.split("\n") if l],
                image="cover.hero", family="globe"))

    # keep the blocks that earn a place, in deck order
    by_id = {b["block_id"]: b for b in r["blocks"]}
    chosen = []
    for bid, name in BLOCK_ORDER:
        b = by_id.get(bid)
        if not b or not (b["findings"] or _lead_prose(b)):
            continue
        if b["relevance"] in DROP and not include_optional:
            continue
        chosen.append((bid, name, b))
    chosen = chosen[:max_sections]

    contents = [(str(i + 1), name, 0) for i, (_b, name, _x) in
                enumerate(chosen)]
    if forecast:
        contents.append((str(len(contents) + 1), "The forecast", 0))
    add(S.contents(contents, title="Contents", subtitle=strap))

    # the opening argument, if the research wrote one
    if r.get("executive_summary"):
        add(S.prose([("The proposition", r["executive_summary"])],
                    title="In one page",
                    subtitle="%s to %s" % (origin, dest) if origin else None,
                    source="Source: as cited in the sections that follow."))

    for i, (bid, name, b) in enumerate(chosen, start=1):
        section = "Section %d - %s" % (i, name)
        add(S.divider(number=i, title=name, strap=_lead_prose(b)[:180] or None,
                      image="divider.%s" % bid,
                      subjects=_subjects(bid, origin, dest),
                      family=BLOCK_FAMILY.get(bid, "field")))
        for sl in _block_slides(b, name, section, bid=bid, figures=figures,
                                fig_sources=fig_sources):
            add(sl)

    if forecast:
        for sl in _forecast_slides(forecast, len(chosen) + 1,
                                   figures=figures, route_facts=route_facts):
            add(sl)

    # The three slides that close every deck, whatever the route. John's ruling of
    # 6 August: the legacy generator carried these and the Observatory path did not,
    # so switching over would have produced a better looking, thinner document.
    why_rows, why_source = _why_rows(chosen, forecast_line)
    n = len(chosen) + (2 if forecast else 1)
    add(S.divider(number=n, title="Method and assumptions",
                  strap="How the forecast was produced and what it rests on",
                  image="divider.method", family="instruments"))
    section = "Section %d - Method and assumptions" % n
    add(S.prose(METHODOLOGY, section=section, title="Methodology",
                source="Source: Avia Cortex QSI methodology."))
    if assumptions:
        add(S.grid([(a, str(b)) for a, b in assumptions], section=section,
                   title="Key assumptions",
                   subtitle="Change any of these and the forecast changes",
                   source="Source: Avia Cortex, run inputs."))
    if why_rows:
        add(S.grid(why_rows, section=section, title="Why this route",
                   source=why_source))

    add(S.thanks(title="Thank you",
                 strap="Prepared by %s for %s." % (publisher, prepared_for),
                 image="closing.frame", family="globe"))

    S.paginate(spec)
    return spec


def _block_slides(b, name, section, bid=None, figures=None,
                  fig_sources=None):
    """One research block becomes a lead slide, its figures, then its evidence.

    The figure sits after the lead prose and before the tables. The prose makes
    the claim, the chart shows it, and the numbers back it up: a chart printed
    after three tables of the same material is a repeat rather than evidence.
    """
    out = []
    lead = _lead_prose(b)
    numeric = [f for f in b["findings"] if _is_display_number(f)]
    plain = [f for f in b["findings"] if not _is_display_number(f)]

    # the strongest numeric finding leads as a callout on the prose slide
    if lead:
        callouts = []
        if numeric:
            top = numeric[0]
            # The callout used to be the value plus the first clause of the claim,
            # lowercased, which produced "$268.4B, austin's metropolitan economy
            # produced..." : a proper noun in lower case, cut mid-sentence, and the
            # figure repeated inside its own callout. The caption is written for
            # exactly this slot, sentence case, and does not repeat the figure.
            # The caption is written for a 90-character slot on the key-numbers
            # slide; the callout beside a prose block is narrower, so it is trimmed
            # to the budget at a sentence boundary rather than mid-word.
            _line = _clause(top["caption"] or top["claim"],
                            S.BUDGET["callout_line"] - len(_value_label(top)) - 3)
            callouts = [S.callout(["%s. %s" % (_value_label(top), _sentence(_line))],
                                  tone="accent")]
        panels = []
        if plain[:3]:
            panels = [S.panel("Also on the record",
                              [_sentence(f["claim"]) for f in plain[:3]],
                              tone="neutral")]
        out.append(S.prose([(None, lead)], panels=panels, callouts=callouts,
                           section=section, title=name,
                           source=_sources_line(b["findings"])))
        numeric = numeric[1:] if numeric else []
        plain = plain[3:]

    # The source goes UNDER the figure in house typography, not inside the PNG.
    # I built it the other way first and the build audit was right to flag five
    # unsourced figure slides: a line printed inside the image at 7pt in the
    # chart's own font is not an Avia source line. deck_figures returns the
    # attribution with each chart and leaves it off the image.
    for slot in BLOCK_FIGURES.get(bid or "", []):
        path = (figures or {}).get(slot)
        if path:
            out.append(S.figure(path, section=section,
                                title=FIGURE_TITLE.get(slot, name),
                                source=(fig_sources or {}).get(slot)
                                       or SOURCE_FALLBACK))

    for chunk in _chunk(numeric, MAX_KEYNUMBERS):
        if not chunk:
            continue
        out.append(S.keynumbers(
            [(_value_label(f), _statement(f)) for f in chunk],
            section=section, title="%s in numbers" % name,
            source=_sources_line(chunk)))

    for chunk in _chunk(plain, MAX_GRID_ROWS):
        if not chunk:
            continue
        out.append(S.grid(
            [(_head(f["claim"]), _statement(f)) for f in chunk],
            section=section, title=name if not out else "%s, continued" % name,
            source=_sources_line(chunk)))
    return out


def _forecast_slides(fc, number, figures=None, route_facts=None):
    """The quantitative core, from a deck_contract-shaped dict.

    The two figures go here rather than earlier in the deck. The research
    sections argue that a market exists; this section is where the deck turns to
    what would be flown, and both figures are about the flying. A route map on
    slide two is decoration, because nothing has yet been proposed for it to
    illustrate. The same map opening this section frames the numbers that follow
    it, and it is the only page that states the sector distance and block time.
    """
    figures = figures or {}
    section = "Section %d - The forecast" % number
    src = fc.get("source") or SOURCE_FALLBACK
    out = [S.divider(number=number, title="The forecast",
                     strap="Avia's central planning case",
                     image="divider.forecast", family="instruments")]

    if figures.get("route_map"):
        out.append(S.figure(figures["route_map"],
                            bullets=list(route_facts or []),
                            title="The route", section=section,
                            source="Source: AviaSolutions analysis. Great "
                                   "circle track, drawn to scale."))

    summary = fc.get("summary") or {}
    stats = summary.get("stats") or []
    if stats:
        out.append(S.stat_row(
            [tuple(s) if isinstance(s, (list, tuple)) else
             (s.get("label", ""), s.get("value", ""), s.get("accent", False))
             for s in stats],
            table=summary.get("schedule"),
            callouts=[S.callout([c]) for c in (summary.get("callouts") or [])],
            title="Summary of the proposition",
            section=section, source=src))
    # What kind of forecast this is: which airline was in it, and whether the
    # market was measured or modelled. Both change the number materially and
    # neither used to appear anywhere on a slide. This does NOT decide what to
    # forecast; the user's own run decides that. It states the basis of whatever
    # run it was handed, so the reader knows which question was answered. Its own
    # page, because it does not fit a callout and must not be a footnote.
    if summary.get("basis"):
        out.append(S.prose([("How to read this forecast", summary["basis"])],
                           callouts=([S.callout(summary["basis_range"],
                                                tone="accent")]
                                     if summary.get("basis_range") else []),
                           title="The basis of the forecast", section=section,
                           source=src))

    if figures.get("demand_build"):
        out.append(S.figure(figures["demand_build"],
                            title="Where the traffic comes from",
                            section=section, source=src))

    for key, title in (("segments", "Point to point demand"),
                       ("connecting_hub", "Connecting over the hub"),
                       ("revenue", "Revenue forecast")):
        t = fc.get(key)
        if t:
            # the segments table renames itself when the chart has taken its
            # volume rows, so the two pages do not read as the same page twice
            out.append(S.table(t, title=t.get("title") or title,
                               section=section, source=src))
    return out


def annex_gaps(research):
    """Data gaps, for the internal annex. Never for the client deck."""
    r = _as_dict(research)
    rows = []
    for b in r["blocks"]:
        for g in b["data_gaps"]:
            rows.append((b["block_name"] or b["block_id"], g))
    for b in r["blocks"]:
        for f in b["findings"]:
            if f["is_single_source"]:
                rows.append((b["block_name"] or b["block_id"],
                             "Single source: %s" % f["claim"]))
    return rows
