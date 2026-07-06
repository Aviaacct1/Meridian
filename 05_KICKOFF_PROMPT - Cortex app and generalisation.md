# First prompt for the next QSI / Avia Cortex chat

Paste the text below the line into the new chat as the first message, with the `app` folder and the handover in the project. It sets the context, the rules, and the first task, and tells the assistant to confirm the plan before building.

---

We are continuing Avia Solutions' QSI route-forecasting tool, now becoming the "Avia Cortex" product. Before doing anything, read, in order: `QSI Project Handover Note - 29 June 2026.md`, then the project memory files (especially `qsi-catchment-design`, `qsi-cortex-frontend`, `qsi-aircraft-economics`). They are the full context. The engine and a working single-route app already exist in the `app` folder.

Where we are: the forecasting engine is built and validated end to end on Genoa-New York from our own data (GeoNames population, OSRM road times, a catchment calibrated to the Sabre point-of-origin split, bounded demand, implied load factor, route and annual P&L). There is a working local web app (`cortex_app.py` + `cortex_dashboard.html`, FastAPI, light "Avia Cortex" SaaS styling) that drives the real engine with live sliders for the Genoa case. A general engine `route_engine.py` runs any city pair but is not yet trustworthy.

The goal: a working forecast tool where you enter ANY two cities and it produces the full forecast and aircraft economics, in the Cortex app, eventually hosted privately at aviacortex.com for the team to test.

How I want you to work:
- Confirm the plan with me before writing code. At each step tell me what you intend and what you expect to see, then proceed once I agree.
- Validate-first. The Genoa-New York case is the calibrated benchmark; do not change the QSI method or the calibrated catchment parameters. Treat any general-engine output as an estimate until it reproduces sensible numbers against a known case.
- Be honest when a result is rough or wrong, and say why. I would rather catch it than show the team a bad number.
- Generated files: author and last-modified-by "Avia Solutions", UK English, no em dashes, "12.4m passengers", "29 June 2026".
- The sandbox mount can serve stale/truncated copies of just-edited files; treat the edit tools as authoritative and write full modules to /tmp when testing.

The first task: make `route_engine.assess` trustworthy for any city pair. Three fixes, all using the OAG store now loaded in `oag.duckdb` (17 weeks): (1) restrict the competing airports to those with real scheduled service from OAG, so the radius stops sweeping in tiny airfields and the wrong hubs (Bristol's 250 km currently pulls in all of London); (2) resolve a city to its main commercial airport(s), so "New York" is JFK/EWR/LGA, not a minor field; (3) add a propensity / demand-sizing model, calibrated to the Genoa benchmark and refined against Sabre where a market has data. Then re-run Genoa-New York through the general path and confirm it reproduces sensible numbers. Do not wire it into the app or touch hosting until the three fixes hold.

When you have read the handover and memory, summarise back to me, in your own words, what the tool is, what the working app does today, and exactly how you will approach the three fixes in task one. Then wait for me to confirm before building.

---

## Notes for you, John, not part of the prompt

The first signal is the summary it gives back. If it understands that the engine is general but the airport-selection and demand-sizing are what make arbitrary routes untrustworthy, let it run task one. If it thinks the job is just "wire two text boxes to the engine", correct it before it builds.

Task one is mostly judgement about airport selection and demand sizing, not plumbing. The OAG store is the right source for "which airports actually have service"; make it use that, not a raw radius. Demand propensity is the genuinely hard input, expect an estimate for arbitrary routes, calibrated up only where Sabre data exists. Keep Genoa-New York as the line: until the general path reproduces a sensible Genoa number, treat any other route it produces as unproven.

Only after task one holds should it wire `route_engine` into `cortex_app` (any-two-cities) and then package for the private aviacortex.com deploy (Dockerfile, requirements, basic-auth gate).
