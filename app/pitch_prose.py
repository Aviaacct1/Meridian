#!/usr/bin/env python3
"""Avia Cortex - the writing pass over researched findings.

The research half returns facts. A deck built from facts alone reads as evidence
with no argument attached: five numbers on a page and nothing saying why they
matter to this route. This is the half that cannot be a script, and it is why
deck generation is a hosted model-backed service rather than a local tool.

What it does NOT do is supply fact. Every figure in the written text must already
appear in the findings handed in. The prompt says so, and `check_no_new_figures`
tests it afterwards by pulling every number out of the written text and looking
for it in the findings. A paragraph that introduces a figure of its own is
rejected and the section falls back to having no prose, which the run report
already flags. Silence is the correct failure here; invention is not.

Register: this is a sales document for an airline or an airport, not a diligence
report. The counter-case, the failed comparables and the data gaps belong in the
internal annex, never on the slide.

Avia Solutions Limited. All rights reserved.
"""
import os
import re

MODEL = os.environ.get("AVIA_PROSE_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.environ.get("AVIA_PROSE_MAX_TOKENS", "1200"))

HOUSE = (
    "Write in Avia Solutions house style.\n"
    "- UK English throughout: organisation, finalised, programme, behaviour, analyse.\n"
    "- No em dashes and no en dashes. Use a comma, a full stop, a semicolon or a colon. "
    "A plain hyphen for ranges.\n"
    "- Active voice by default. First person plural for analytical commentary, we consider, "
    "we have assumed. Impersonal for findings, it is forecast that, it is expected that.\n"
    "- Avia hedging: circa rather than approximately; broadly and largely, used sparingly.\n"
    "- Numbers as 12.4m passengers, $695m, circa 9% of total traffic. Dates as 29 April 2026 "
    "with no ordinal suffix.\n"
    "- Banned words and phrases: robust, leverage, synergy, going forward, deep dive, crucial, "
    "playbook, cohort, guardrail, defensible, thesis, unlocks, sweep, gate, lever, over-index, "
    "at the end of the day, fantastic opportunity.\n"
    "- Banned connectives: Furthermore, Moreover, Additionally, Interestingly, In conclusion, "
    "In summary, Ultimately, When it comes to. However and Therefore and Notably are fine.\n"
    "- No AI tells: no It is important to note, no It is worth noting, no negative parallelism "
    "of the form it is not X it is Y, no three-part adjective lists, no Title Case headings.\n"
)

SYSTEM = (
    "You are a route development analyst at Avia Solutions, an aviation consultancy, writing the "
    "argument that sits above the evidence on a slide in an airline route pitch. You are given "
    "the verified findings for one section and nothing else. You write the case those findings "
    "support.\n\n"
    "ABSOLUTE RULE: every figure you write must appear in the findings you were given. You may "
    "not add a figure from your own knowledge, you may not estimate, and you may not round a "
    "figure into a different number. If the findings do not support a sentence, do not write it. "
    "A short paragraph that is entirely supported beats a long one that is not.\n\n"
    "This is a sales document. Make the case for the route. Do not argue the case against it, do "
    "not list what the research failed to find, and do not caveat. That material goes to a "
    "separate internal annex.\n\n" + HOUSE
)

BLOCK_ANGLE = {
    "economic_context": "the size and direction of the two economies the route would join",
    "corporate_links": "the named companies and sectors that would buy the front cabin",
    "trade": "the trading relationship that already exists without an air link",
    "tourism": "the visitor demand in both directions and what it is worth",
    "diaspora": "the settled community that generates year-round visiting friends and relatives",
    "education": "the university and student flows that fill the shoulder months",
    "passenger_profile": "who travels this market today and how they travel",
    "airport_overview": "the airport's ability to take the service and its recent record",
    "non_cannibalization": "why the service adds traffic rather than moving it",
    "case_study": "the comparable route that has already proved this works",
}

_NUM = re.compile(r"\d[\d,\.]*\s*(?:%|bn|m\b|k\b)?", re.I)


def _numbers(text):
    """Every numeric token in a piece of text, normalised for comparison."""
    out = set()
    for m in _NUM.finditer(text or ""):
        t = m.group(0).strip().lower().replace(",", "").replace(" ", "")
        if t and not re.fullmatch(r"[\.]+", t):
            out.add(t.rstrip("."))
    return out


def check_no_new_figures(text, findings):
    """Figures in the written text that are not in the findings. Empty is good.

    Years are allowed through: a sentence may date a claim the findings date, and
    the year is carried on the finding's own year field rather than in its claim.
    """
    allowed = set()
    for f in findings or []:
        for field in ("claim", "caption", "value", "year", "relevance_to_case"):
            allowed |= _numbers(str(f.get(field) or ""))
    stray = []
    for tok in _numbers(text):
        if tok in allowed:
            continue
        if re.fullmatch(r"(19|20)\d{2}", tok):      # a year, not a claim
            continue
        # 4.6m against a finding of 4600000, and the reverse
        if any(tok.rstrip("mbnk%") == a.rstrip("mbnk%") for a in allowed):
            continue
        stray.append(tok)
    return stray


def _prompt(block_name, angle, findings, ctx, words):
    lines = []
    for f in findings:
        bits = [str(f.get("claim") or "").strip()]
        if f.get("value"):
            bits.append("[figure: %s %s]" % (f.get("value"), f.get("unit") or ""))
        if f.get("source_name"):
            bits.append("[source: %s]" % f["source_name"])
        lines.append("- " + " ".join(b for b in bits if b))
    return (
        "Route: %s (%s) to %s (%s). Airline: %s.\n"
        "Section: %s. The angle this section has to carry: %s.\n\n"
        "Verified findings, and the only facts you may use:\n%s\n\n"
        "Write ONE paragraph of %d to %d words, and UNDER 430 CHARACTERS, that states what these "
        "findings mean for this "
        "route. Lead with the point, not with a recital of the numbers. Use at most three of the "
        "figures, chosen because they carry the argument; the slide prints the rest beside you, "
        "so repeating all of them wastes the paragraph. Do not open with the section name. "
        "Return the paragraph only, with no heading and no preamble."
        % (ctx.get("origin_city"), ctx.get("origin"), ctx.get("destination_city"),
           ctx.get("destination"), ctx.get("airline") or "a new entrant",
           block_name, angle, "\n".join(lines), words - 20, words + 20)
    )


def _text_of(resp):
    out = ""
    for blk in (resp.content or []):
        if getattr(blk, "type", "") == "text":
            out += getattr(blk, "text", "")
    return out.strip()


def write_block(client, block_id, block_name, findings, ctx, words=65, model=None):
    """One section's opening argument. Returns (text, note). Text is "" on failure."""
    if not findings:
        return "", "no findings"
    angle = BLOCK_ANGLE.get(block_id, "why this matters to the route")
    try:
        resp = client.messages.create(
            model=(model or MODEL), max_tokens=MAX_TOKENS, system=SYSTEM,
            messages=[{"role": "user",
                       "content": _prompt(block_name or block_id, angle, findings, ctx, words)}])
    except Exception as e:
        return "", "error: %s" % e
    text = re.sub(r"\s+", " ", _text_of(resp)).strip()
    if not text:
        return "", "empty reply"
    stray = check_no_new_figures(text, findings)
    if stray:
        # Rejected rather than repaired. A paragraph that invents a figure cannot
        # be trusted on the ones it did not invent.
        return "", "rejected, figures not in findings: %s" % ", ".join(stray[:5])
    return text, "ok"


def write_executive_summary(client, blocks, ctx, forecast_line="", words=110, model=None):
    """The one-page proposition. Draws on every section that produced prose."""
    paras = [(b.get("block_name") or b.get("block_id"), b.get("presentation_text"))
             for b in blocks if b.get("presentation_text")]
    if not paras:
        return "", "no section prose"
    body = "\n\n".join("%s: %s" % (n, t) for n, t in paras)
    extra = ("\n\nAvia's forecast for the route, which you may quote exactly as written:\n%s"
             % forecast_line) if forecast_line else ""
    prompt = ("Route: %s to %s. Airline: %s.\n\nThe sections of the pitch, already written:\n\n%s%s"
              "\n\nWrite ONE paragraph of %d to %d words that states the proposition for this "
              "route: what the market is, what it would carry, and why now. Use only figures "
              "that appear above. Return the paragraph only."
              % (ctx.get("origin_city"), ctx.get("destination_city"),
                 ctx.get("airline") or "a new entrant", body, extra, words - 20, words + 20))
    try:
        resp = client.messages.create(model=(model or MODEL), max_tokens=MAX_TOKENS,
                                      system=SYSTEM,
                                      messages=[{"role": "user", "content": prompt}])
    except Exception as e:
        return "", "error: %s" % e
    text = re.sub(r"\s+", " ", _text_of(resp)).strip()
    allowed = []
    for b in blocks:
        allowed.extend(b.get("findings") or [])
    if forecast_line:
        allowed.append({"claim": forecast_line})
    stray = check_no_new_figures(text, allowed)
    if stray:
        return "", "rejected, figures not in findings: %s" % ", ".join(stray[:5])
    return text, "ok"


BANNED = [
    "furthermore", "moreover", "additionally", "interestingly", "in conclusion",
    "in summary", "ultimately", "it is important to note", "it is worth noting",
    "robust", "leverage", "synergy", "going forward", "deep dive", "crucial",
    "playbook", "cohort", "guardrail", "defensible", "unlocks", "over-index",
]


def house_style_flags(text):
    """Anything in the written text that would fail the final check before output."""
    flags = []
    low = (text or "").lower()
    if "—" in text or "–" in text or "--" in text:
        flags.append("dash: em, en or double hyphen")
    for w in BANNED:
        if re.search(r"\b%s\b" % re.escape(w), low):
            flags.append("banned: %s" % w)
    for us, uk in (("organization", "organisation"), ("analyze", "analyse"),
                   ("finalized", "finalised"), ("behavior", "behaviour"),
                   ("program ", "programme ")):
        if us in low:
            flags.append("US spelling: %s should be %s" % (us.strip(), uk.strip()))
    return flags
