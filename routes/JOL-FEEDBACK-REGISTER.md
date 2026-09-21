# Jol's layman's read of Meridian (3 September 2026): the 43 items, owner and state

Controller's register, v1, 21 September 2026. Source: /Shared/Company Data/18 Products/QSI/
User comments/Meridian QSI Tool - Jol comments - Sep 2026.docx (Jolyon Kingham, 3 Sep, on the
pre-step-1 build). John, 21 Sep: not every item is adopted; the rulings below say which are.
Owners: W2 the dashboard, catchment and economics pages (cortex_dashboard.html and friends);
W3 the methodology page, pack and deck wording. W4 changes the manual's screen words once,
after the batch lands. Nothing here touches engine demand logic.

## Rulings (John, 21 Sep, with the controller)

R1. "MEASURED" becomes "ACTUAL" on every client surface where a figure is read from data
    (Sabre, OAG, DOT): sources, chart titles, table headers, the catchment page. John: in air
    service development "measured" implies an estimate; "actual" means observed fact. The
    three-classes-of-number framing (Nick's note, deck slide 4, manual section 2) is renamed
    "actual, calibrated, capped" subject to Nick's agreement, which John asks for; until Nick
    answers, slide 4 and manual section 2 keep Nick's words and everything else changes.
R2. "PHYSICS" goes: "seat cap" where the cap is the seats offered, "hard cap" elsewhere, and
    never "physics" on any client surface, including the methodology bridge bar (W3, with the
    other three label changes already ruled).
R3. Items 9 and 11 need plain labels: W2 reads what "steady state" and "Aggressive (type
    +0.20)" do in code and proposes a label and a one-line hover for each in W2-STATUS; the
    controller approves the words. "Steady state" is likely "the route's mature year"; say so.
R4. THE CATCHMENT PAGE is part of the full tool and on the demo path; Nick and Jol agree it is
    unclear. It is rewritten before the freeze: W2 rebuilds the page's text to say, for the
    airport shown, the resident population by drive time, the share Meridian assumes the
    airport captures and why (survey or mobility data where it exists, the model otherwise),
    and the biggest destination markets a nonstop could win back; "via home" and "EW" are
    written out; the 220 km population line is either explained or dropped (W2 reads the code
    and says which); the page opens on the route loaded on the dashboard, never on SJC (bug
    31). Nick reads the rewritten page before the freeze.
R5. EACH-WAY AND TWO-WAY is the most important item on the list (John: the TPE work went wrong
    on exactly this; US readers expect departing passengers, most of the world two-way). Two
    parts. (i) MANDATORY before the freeze: every passenger figure on every surface (dashboard
    outputs, charts, tables, pack, PDF, workbook, deck) carries its basis in its own label,
    "each way" or "two-way", never implied. (ii) A basis switch on the dashboard, "Show: each
    way | two-way", display only, both from the same number, default each way (the engine's
    basis) with the label; W2 builds it before the freeze if it is a display change and says
    so if it is not. The workbook already carries both.
R6. Bugs (12, 31, 32, 33) are fixed before the freeze; 33 is fixed by naming the catchment the
    table covers ("nonstop Paris service from the London catchment, which includes BHX") if
    the airport is legitimately in the catchment, and by filtering if it is not.
R7. Names beside codes (15, 29): W2 says in its next STATUS whether the lookups make it a
    one-session change; if yes, before the freeze; if no, after Routes.
R8. Copy and label items are adopted as Jol wrote them unless a ruling above changes the word,
    with one exception: 18 and 22's source lines end "(actual)" not "(ACTUAL)"; house style.

## The items

| # | Surface | Jol's point | Group | Owner | Ruling |
|---|---|---|---|---|---|
| 1 | Dashboard | "Enter a city or airport for each end" wording | B | W2 | Adopt |
| 2-5 | Dashboard | ORIGIN AIRPORT, DESTINATION AIRPORT, DEP TIME, RETURN ARR TIME | B | W2 | Adopt |
| 6 | Dashboard | TURNAROUND (MIN) ambiguous | B | W2 | "Turnaround, minutes" |
| 7-8 | Dashboard | CURFEW TIME AT ORIGIN / DESTINATION | B | W2 | Adopt |
| 9 | Dashboard | "2025 - steady state" unclear | C | W2 | R3 |
| 10 | Dashboard | SEAT COUNT next to AIRCRAFT | B | W2 | Adopt if layout allows |
| 11 | Dashboard | "Aggressive (type+0.20)" unclear | C | W2 | R3 |
| 12 | Dashboard | error banner until the arrow is clicked | A | W2 | Fix |
| 13 | Dashboard | label or hover on the market-background arrow | B | W2 | Adopt ("Route detail") |
| 14 | Outputs | two-way beside each-way | C | W2 | R5 |
| 15 | Outputs | carrier name beside code | D | W2 | R7 |
| 16 | Methodology, everywhere | "measured" to "actual" | C | W3, W2, W4 | R1 |
| 17 | Methodology, everywhere | "physics cap" | C | W3, W2 | R2 |
| 18 | P2P chart | source line | B | W2 | Adopt, R8 |
| 19 | P2P chart | two-way passengers | C | W2 | R5 |
| 20-21 | Market chart | title and "today" | B | W2 | Adopt |
| 22 | Cabin mix chart | source line | B | W2 | Adopt, R8 |
| 23-25 | Connecting chart | title, subtitle, sentence | B | W2 | Adopt |
| 26-28 | Nonstop table | title, subtitle, DEP TIME (LOCAL) incl. CSV | B | W2 | Adopt |
| 29 | Nonstop table | names beside codes | D | W2 | R7 |
| 30 | Catchment box | 220 km v drive time | C | W2 | R4 |
| 31 | Catchment page | always opens on SJC | A | W2 | Fix |
| 32 | Output tabs | do nothing | A | W2 | Fix |
| 33 | Nonstop table | BHX under London-Paris | A | W2 | R6 |
| 34 | Heads up | sentence | B | W2 | Adopt |
| 35-41 | Catchment page | unclear throughout; "via home"; "EW" | C | W2 | R4 |
| 42-43 | Economics page | top text, route box text | B | W2 | Adopt |

## State

v1: register written; rulings issued to W2 and W3 (their rulings files); W4 told the screen
words change once in one batch. State per item is updated from W2 and W3 STATUS files.
