# QSI Tool — Handover Note

**Date:** 29 June 2026
**Author:** Avia Solutions
**Supersedes:** "QSI Project Handover Note - 27 June 2026.md" (still valid for engine detail). Read this first, then the project memory.

---

## 1. Where we are in one paragraph

The forecasting engine is built, validated and runs end to end on a real route. Genoa-New York is proven from your own data: GeoNames population, OSRM road times, a catchment calibrated to the Sabre point-of-origin split (SSE 0.0009), a bounded route demand, the implied load factor, and the route and annual P&L. There is a working local web app (Avia Cortex) that drives the real engine with live controls, three client decks (forecast+P&L, plain-English explainer, and a tool-generated deck), and the OAG schedule store is freshly loaded (17 twice-yearly weeks, 2015-2026). The next build is generalising the route case so the app assesses ANY two cities, then putting it behind aviacortex.com.

The realistic Genoa-New York case: daily A321XLR, ~85% load, ~11% margin, 74% breakeven, ~$5.5m a year.

---

## 2. The product direction (decided 29 June)

- **Brand: Avia Cortex**, the platform, with the tools as named products inside it (Route Forecasting live; Fleet Economics, Network Planning, Catchment Studio to come). Domain **aviacortex.com**; redirect avia-analytics.com and aviaintellect.com to it (one identity, not separate brands).
- **Look: light, clean, modern SaaS**, navy `#1F3864` + accent `#2F6BF0` + green. The prototype and the live app already use it. Drop in the real logo/fonts when available, or refine here and roll back into the Avia brand for consistency.
- **Architecture: API in the middle.** Python engines stay the engine; a thin FastAPI service exposes them; the web front end calls it. Look and engine evolve independently.
- **Hosting:** publish to a password-gated subdomain (demo./app.aviacortex.com). The app is self-contained (no 15 GB Sabre at run time), so it deploys light. "Non-indexed" is not private — gate it, the method and data are commercially sensitive. Report drafting can work hosted with a server-side Anthropic API key; static PPTX/XLSX need no AI.

---

## 3. The working app and the general engine

- `cortex_app.py` — FastAPI. Loads the baked Genoa case at startup, serves the dashboard, and `/api/assess` re-runs the real engine (bounded repatriation → implied LF → route P&L) per request. Run: `pip install fastapi uvicorn` then `uvicorn cortex_app:app --port 8000`, open localhost:8000.
- `cortex_dashboard.html` — the live Avia Cortex dashboard; sliders (capture, frequency, fares, aircraft, incentive) re-fetch and re-render the bars, funnel and P&L.
- `route_engine.py` — **the general engine: `assess(origin, dest, ...)` for ANY city pair.** Built and validated (Bristol-NY, Edinburgh-Boston, Genoa-NY). Resolves airports via `airportsdata`, finds competing airports near the origin, builds the GeoNames catchment, allocates with the Genoa-calibrated parameters, sizes demand by a propensity, runs economics on the great-circle sector. **Foundation works; needs three fixes before it is trustworthy (see section 5, item 1).**

---

## 4. Engine modules (app/), all validated

Demand: `qsi_score.py` (single QSI scorer), `oag_store.py` (SQL legs from oag.duckdb), `run_multihub_qsi.py`. Catchment: `catchment.py` (drive-time + generalised-cost choice, calibrated `att_exponent`/`logit_scale`/VoT), `geonames.py` (offline population), `routing.py` (OSRM/ORS road times, cached), `route_demand.py` (`calibrate_service_values`, `bounded_repatriation`). Economics: `aircraft_economics.py` (current-data cost stack; E190 Maverick validation holds), `economics_slide.py`, `route_deck.py`, `output_workbook.py`. Orchestration: `route_assessment.py`, `genoa_nyc.py`, `calibrate_genoa.py`, `sabre_catchment.py`. Ingest: `oag_ingest.py` / `ingest_all_oag.py` (now enumerates with `os.listdir`, not `glob` — the Egnyte virtual drive defeats glob), `sabre_ingest.py`.

Data stores: `oag.duckdb` (~165 MB, 17 weeks loaded), `sabre.duckdb` (~15 GB, on C:\Avia).

---

## 5. What is left, in priority order

1. **Make `route_engine` trustworthy for any pair (the priority).** Three fixes, all using the OAG store now loaded: (a) restrict competing airports to those with real scheduled service from OAG (raw radius sweeps in tiny airfields and the wrong hubs — Bristol's 250 km pulled in all of London); (b) resolve a city to its main commercial airport(s) (New York resolved to NYS, not JFK/EWR/LGA); (c) a propensity / demand-sizing model calibrated to the Genoa benchmark, refined against Sabre where a market has data. Then point `cortex_app` at `route_engine.assess` → the any-two-cities app.
2. **Package for deploy.** Dockerfile, requirements, a basic-auth gate, a deploy config. Then you/IT do the hosting account and DNS for aviacortex.com.
3. **Firm the Genoa case inputs.** Cabin mix (premium share/fare) is the last judgement input; confirm the Sabre fare basis; consider the capture rate (0.65 assumed).
4. **Catchment refinements (final product).** Nice with a border penalty (the natural catchment runs a little high); sharper access sensitivity so the route scenario stands without the hand bound; isochrone-summed raster population (GHS-POP/Kontur) only if the centroid proxy proves materially off.
5. **Local consolidation.** Point `qsi_market`/`QSIEngine` at `qsi_score`; SJC-HKG acceptance test (~65.6%); re-point `goa_nyc_forecast`.
6. **Data + launch.** Load Sabre 2025; assumptions-register citation sweep.

**Start the next chat on item 1.** See the kickoff prompt: `05_KICKOFF_PROMPT - Cortex app and generalisation.md`.

---

## 6. Principles to preserve

QSI formula frozen (validate first, then improve). Every key input user-overridable with sensible auto-defaults. Offline must work. Economics is directional (disclaimer on every economics output). Citation-first. Generated files: author and last-modified-by = "Avia Solutions", UK English, no em dashes, "12.4m passengers", "29 June 2026".

---

## 7. Recurring sandbox note

The OneDrive/Egnyte mount can serve a stale or truncated copy of a just-edited file to the Linux shell (the file-edit tools are authoritative). When testing, write the full module to `/tmp` via heredoc, or read with the file tools, rather than trusting a `cp` of a just-edited file. Memory files: `qsi-project-state`, `qsi-catchment-design`, `qsi-cortex-frontend`, `qsi-aircraft-economics`, `qsi-method-improvements`, `qsi-knowledge-assets`, `qsi-oag-scope`, `qsi-open-judgement-calls`, `qsi-people`.
