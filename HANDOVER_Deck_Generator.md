# Handover - Route Forecast Deck Generator (new chat)

**Purpose of this note:** start the deck-generation work in a fresh chat. This conversation stays reserved for tomorrow's OAG calibration once the full data is loaded. Paste this note in to begin.

## The task

Build the wider PowerPoint deck that presents a route forecast, replicating Avia's bespoke client decks end to end. In the old POC this was done in steps: an 8-12 category research search was drafted by the tool, cut and pasted into Claude (or another AI), and the results pasted back to assemble a master PPT. The goal now is to do that properly inside the tool.

**Two challenges, in order:**

1. Content quality first. Replicate what Avia produces for paid projects. Accept airport-supplied uploads (SJC likes photos of the Google, Apple and NVIDIA buildings) and place them. Produce a finished `.pptx`.
2. Then productionisation. Work out how to ship it: connect the tool backend to Claude as a professional tool, or ship an LLM with the tool that does the web research locally wherever it runs.

## Decisions already made (John, 28 June 2026)

- **First worked deck: British Airways, London (LHR-SJC).** Benchmark primarily against the ORIGINAL 2015 deck that first won BA to the route, and also look at the 2025 re-pitch - the two a decade apart are both useful templates and show how the house style evolved. Pull from the POC work to see what was done before.
- **First build produces a full end-to-end `.pptx`:** research narrative + our forecast tables + labelled photo-upload slots, a complete deck to open and critique.
- Production deployment (challenge 2) comes after the content quality is proven.

## Where to start (Egnyte)

- **BA primary benchmark - the ORIGINAL 2015 winning deck:**
  - Final pitch (PDF): `British Airways Pitch LHR-SJC 09Mar15.pdf` entry `dd17ec1b-1752-467d-8d69-427255335b23`
    path `/Shared/Company Data/07 Current Projects/San Jose - Route Development/Target Airlines/British Airways/Mar 2015/Presentation/Final presentation Mar 2015/`
  - Editable master forecast slides (Ollie): `British Airways Master forecast slides (OS) 06Mar2015.pptx` entry `fa3e3c68-2f6c-4c45-917a-575180896ea3`
  - Full master with all imagery (61MB): `British Airways Master 16Feb2015.pptx` entry `5b5c547e-d9d9-471d-95e3-e0b54ea07c14`
  - What it contains: P2P 249,800 / connecting over London 904,500; 43% premium, $3,600 average return fare, 38% BA market share; capacity 155,792 at 84-92% LF across versions; Mayor Sam Liccardo endorsement; economic-impact case (+46,000 jobs, £12bn by 2024, Oxford Economics 2014); India connections deliberately EXCLUDED to stay conservative. This is the template that actually won the route.
- **BA secondary benchmark - the 2025 re-pitch (10 years on):** `British Airways LHR-SJC (Forecast and Links) 16May2025.pptx`
  entry `958877aa-c7f8-48b6-b364-d594fae27774`
  path `/Shared/Company Data/07 Current Projects/San Jose - Route Development/Target Airlines/British Airways/May 2025/Pitch/old/`
- **The POC work / product docs:** `/Shared/Company Data/18 Products/QSI/Documentation/`
  - `00_START_HERE.md` entry `13f22222-dfeb-4e62-a31d-4b41601d4019` (the Christmas-2025 Streamlit POC; the generator vision)
  - `04_COWORK_KICKOFF_PROMPT.md` entry `2b6d3dff-474d-45b3-bc24-7e04884ac798` (POC entry point `app/avia_qsi_auto_v3.py`)
  - Read the rest of the numbered docs in that folder; the prior category-search and deck-assembly approach is described there. Recover the original 8-12 category search prompt if it is in these files.

## The deck anatomy (recovered from the real decks)

A bespoke deck splits into two halves. The **quantitative core is already produced by the forecast tool** in `app/` (this project): point-to-point, connecting-beyond-hub, connecting-behind-SJC, route economics, methodology. The **qualitative half is the category research.** From the Korean Air deck (43 slides) the sequence is:

1. Cover - "Opportunity to Serve Silicon Valley & The Bay Area from [City]"
2-3. Airline strategic hook (fleet, alliances, regulatory/merger situation, slot position)
4-5. Why this airline / why SJC; no cannibalisation of SFO
6-10. **Forecast core** (summary year 1; P2P; connecting beyond hub; connecting behind SJC) - FROM THE TOOL
11-13. Market background: connecting patterns, seasonality
14-17. Why San Jose - better located, market fundamentals, 89% business preference, campus distances
18-22. Silicon Valley economic strength - Google HQ expansion, manufacturing employment, economic indicators, tech employers/salaries/GDP, top 30 tech firms
23-30. Links between Silicon Valley and the destination - trade/investment/tech/tourism/education, senior engagement, business roundtables, named deals, company presence, the destination's own tech valley, accelerators
31-32. Onward links (e.g. China links, Asian population proximity)
33-38. Methodology (forecast, schedule, P2P, connecting, catchment) - FROM THE TOOL
39-43. Appendix (alternative frequency scenario)

### The 8-12 research categories (the qualitative search)

Derived from the deck titles, to be confirmed against the POC's original prompt:

1. Airline situation and strategic hook (fleet, alliances, regulatory, current network gap)
2. Why SJC over SFO/OAK (business preference, slot availability, location, campus proximity)
3. Silicon Valley economic strength (GDP, household income, Fortune 500, employment)
4. Tech employers and HQs (top firms, campus locations, expansions)
5. Destination <-> Silicon Valley trade and investment links (FDI, trade figures)
6. Named partnerships and deals (roundtables, accelerators, marquee investments)
7. Diaspora / VFR population in the Bay Area (ethnic population, visitor numbers)
8. Education and university links
9. Cultural links (content, sister cities, events)
10. Destination's own innovation ecosystem (e.g. Pangyo for Seoul)
11. Onward connectivity rationale (the connecting markets the forecast captures)
12. Seasonality / market fundamentals

Each category becomes 1-3 slides, researched with current facts and figures (web search), written to Avia's bespoke quality, with sources.

## What we already have to wire in

- **The forecast tool** in `app/` (this project): produces the P2P, connecting-feed and economics outputs. Validated against the analyst forecasts and real outturn (BA SJC-LHR model 125,463 vs analyst 129,162 vs actual carried 116,838).
- **Connecting-feed layer** built (`app/connecting_feed.py`); calibration in progress, see the QSI memory. NOTE: connecting capture is route-specific - do not over-generalise.
- **Four deck fixtures** (CI/BR/KE/CA) with full per-city connecting tables in `app/*_connecting_fixture.json` - useful as content/quality references.
- **The `pptx` skill** for building the deck; the `docx` skill if the research content is drafted as a document first.

## Photo / asset uploads

The deck must accept airport-supplied images (SJC: Google, Apple, NVIDIA buildings) and place them on the relevant slides (the "Why San Jose" and tech-employer sections). For the first build, use clearly labelled placeholder slots showing where each upload goes, and let the airport drop images in.

## Suggested first steps in the new chat

1. Read the BA benchmark deck and the POC docs folder; recover the original category-search prompt.
2. Pull the BA SJC-LHR forecast outputs from the tool for the quantitative slides.
3. Run the 12-category research for the BA/London case (web search, current figures, sources).
4. Assemble a full `.pptx` mirroring the deck anatomy, with photo-upload slots.
5. Compare side by side with the BA benchmark deck; tune to quality.
6. Only then, scope challenge 2 (production: Claude backend vs shipped local LLM).

## Reminders

- Generated files: set document author and last-modified-by to "Avia Solutions"; verify before delivery.
- UK English, John's house style (no em/en dashes, "circa" not "approximately", etc.).
- This conversation continues with the **OAG calibration** tomorrow when the full OAG data is loaded - keep that separate from the deck work.
