#!/usr/bin/env python3
"""Offline test of the figure slot in the research sections.

    py -3.12 test_block_figures.py

The gap this closes, John 7 August: the generated deck carried tables and
numbers and not a single figure, so ten research sections ran about 60% empty.

What is checked is placement and restraint. A figure has to land in the section
whose argument it carries, after the prose that makes the claim and before the
tables that back it up, and a section with no figure has to be left exactly as
it was. A generator that quietly drops a grey placeholder onto every empty page
would pass a "the deck has figures" test and fail the only one that matters.

Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_from_research as SR

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-58s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def finding(claim, value, caption=None):
    return {"claim": claim, "value": value, "caption": caption or claim,
            "source": "Test fixture", "url": "", "date": "2026"}


def block(bid, summary, n=4):
    return {"block_id": bid, "relevance": "core", "summary": summary,
            "presentation_text": summary,
            "findings": [finding("Finding %d about %s" % (i, bid),
                                 "%d.%dm" % (i, i)) for i in range(1, n + 1)]}


RESEARCH = {"origin_city": "Edinburgh", "destination_city": "Austin",
            "executive_summary": "A test proposition.",
            "blocks": [block("airport_overview",
                             "Edinburgh handled a record year in 2025."),
                       block("passenger_profile",
                             "The traffic is business weighted."),
                       block("non_cannibalization",
                             "No carrier serves this pair today."),
                       block("tourism", "Austin draws festival demand."),
                       block("trade", "Trade between the two is growing.")]}

FIGS = {"airport_pax": "pax.png", "airport_haul": "haul.png",
        "airport_load": "load.png", "airport_airlines": "airlines.png",
        "dest_pax": "dest.png"}


def build(figures, sources=None):
    return SR.build_spec(RESEARCH, codename="Testbed", title="Test",
                         strap="A test", prepared_for="Nobody",
                         figures=figures, fig_sources=sources)


def slides_of(spec, section_word):
    return [s for s in spec["slides"]
            if section_word.lower() in str(s.get("section", "")).lower()]


with_figs = build(FIGS)
without = build({})

# --- 1. the figures land, and in the right sections ---------------------------
imgs = [s["image"] for s in with_figs["slides"] if s["type"] == "figure"]
check("every supplied figure reaches the deck", len(imgs) == 5, imgs)
check("the passenger chart is in the airport section",
      "pax.png" in [s.get("image") for s in slides_of(with_figs, "The airport")],
      [s.get("image") for s in slides_of(with_figs, "The airport")])
check("the load factor is in the who-travels section",
      "load.png" in [s.get("image") for s in slides_of(with_figs, "Who travels")],
      [s.get("image") for s in slides_of(with_figs, "Who travels")])
check("the airline chart is in the cannibalisation section",
      "airlines.png" in [s.get("image")
                         for s in slides_of(with_figs, "cannibalise")],
      [s.get("image") for s in slides_of(with_figs, "cannibalise")])
check("the destination chart is in the visitor section",
      "dest.png" in [s.get("image") for s in slides_of(with_figs, "Visitor")],
      [s.get("image") for s in slides_of(with_figs, "Visitor")])
check("a section with no figure mapped to it gets none",
      not [s for s in slides_of(with_figs, "Trade") if s["type"] == "figure"])

# --- 2. order within a section ------------------------------------------------
apt = [s["type"] for s in slides_of(with_figs, "The airport")]
check("the prose leads, before any figure",
      apt.index("prose") < apt.index("figure"), apt)
check("and the figures come before the tables",
      apt.index("figure") < min([i for i, k in enumerate(apt)
                                 if k in ("grid", "keynumbers")] or [99]), apt)
check("both airport figures appear, in the order given",
      [s["image"] for s in slides_of(with_figs, "The airport")
       if s["type"] == "figure"] == ["pax.png", "haul.png"])

# --- 3. RESTRAINT: no figures means no placeholders ---------------------------
check("with no figures at all, not one figure slide is invented",
      not [s for s in without["slides"] if s["type"] == "figure"],
      [s["type"] for s in without["slides"] if s["type"] == "figure"])
check("and the deck is exactly five slides shorter, no more and no less",
      len(with_figs["slides"]) - len(without["slides"]) == 5,
      (len(with_figs["slides"]), len(without["slides"])))
one = build({"airport_pax": "pax.png"})
check("one figure supplied gives one figure slide",
      len([s for s in one["slides"] if s["type"] == "figure"]) == 1)
check("and the sections that lost theirs are otherwise untouched",
      [s["type"] for s in slides_of(one, "Who travels")]
      == [s["type"] for s in slides_of(without, "Who travels")])

# --- 4. sourcing, once, on the slide -------------------------------------------
# The attribution goes under the figure in house typography. deck_figures leaves
# it off the PNG so it is printed once, and the build audit checks the slide.
sourced = build(FIGS, sources={
    "airport_pax": "Source: ACI airport traffic. AviaSolutions analysis.",
    "airport_load": "Source: OAG schedules for seats, ACI for passengers."})
check("a figure slide carries the source it was given",
      [s.get("source") for s in sourced["slides"]
       if s.get("image") == "pax.png"]
      == ["Source: ACI airport traffic. AviaSolutions analysis."],
      [s.get("source") for s in sourced["slides"] if s.get("image") == "pax.png"])
check("EVERY figure slide is sourced, which is what the build audit checks",
      all(s.get("source") for s in sourced["slides"] if s["type"] == "figure"),
      [(s.get("image"), s.get("source")) for s in sourced["slides"]
       if s["type"] == "figure" and not s.get("source")])
check("a chart with no source supplied still gets the house fallback",
      all(s.get("source") for s in with_figs["slides"] if s["type"] == "figure"),
      [(s.get("image"), s.get("source")) for s in with_figs["slides"]
       if s["type"] == "figure" and not s.get("source")])
check("while the non-figure slides still carry theirs",
      all(s.get("source") for s in with_figs["slides"]
          if s.get("title") in ("In one page", "Methodology")),
      [(s.get("title"), s.get("source")) for s in with_figs["slides"]
       if s.get("title") in ("In one page", "Methodology")])

# --- 5. the mapping is complete and consistent ---------------------------------
mapped = {s for slots in SR.BLOCK_FIGURES.values() for s in slots}
check("every mapped figure has a caption",
      all(s in SR.FIGURE_TITLE for s in mapped),
      sorted(mapped - set(SR.FIGURE_TITLE)))
check("every mapped section is a real block",
      all(b in dict(SR.BLOCK_ORDER) for b in SR.BLOCK_FIGURES),
      sorted(set(SR.BLOCK_FIGURES) - set(dict(SR.BLOCK_ORDER))))
import deck_figures as DF
check("and deck_figures builds exactly the slots the spec places",
      set(DF.AIRPORT_FIGURES) == mapped,
      (sorted(set(DF.AIRPORT_FIGURES) ^ mapped)))

print("\n%d checks, %d failed" % (CHECKS, len(FAIL)))
if FAIL:
    print("FAILED: %s" % ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
