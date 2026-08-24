# Jarek Zych tester feedback, 24 August 2026

Source: Jarek Zych, email to John Carter (cc Jolyon Kingham), 24 August 2026 19:49, subject
"Re: Meridian - The QSI Tool". Captured here in full ahead of the post-holiday development
programme. Prioritisation against Avia's legacy QSI methodology and the wider industry-standard
model is in `JAREK-FEEDBACK-PRIORITISATION-24Aug2026.md`, alongside this file.

One item was investigated same-day rather than left to the list: see the curfew note below.

## Items, as raised

1. **Expert Mode exposure.** Hide Expert Mode behind a permission rather than showing it to every
   user; it adds complexity for users who don't need it.

2. **Calibration against real launches.** Noted approvingly, no action; this is already how the
   calibrated model (behind the "second, calibrated method" in the methodology note) works.

3. **OAG week / Sabre year selection.** Currently a fixed read. Wants the user able to choose the
   OAG week and Sabre year, and a comparison tab across different weeks/years.

4. **Auto-generated market background.** Once origin, destination and airline are chosen, generate
   a market background automatically, before the user enters remaining assumptions or runs
   anything: P2P market, catchment, behind/beyond potential, total demand by airport at a stated
   circuity assumption, cabin/class split, alliance/airline split, existing direct services.
   Downloadable charts/KPIs.

5. **Curfew optimiser, INVESTIGATED 24 August, not a demand bug.** Jarek's read: the optimiser
   finds a theoretical best time, then flags it as restricted, rather than optimising within the
   curfew. Traced through `route_feed.optimise_departure` and `cortex_app._schedule_times`.
   Finding: the departure that actually drives the forecast IS chosen only from curfew-permitted
   times; that part is correct. Two real issues sit underneath what he saw: (a) the function also
   always returns the unrestricted theoretical optimum, by design, so an airport can be shown what
   the curfew costs it, and if the dashboard surfaces that figure without labelling it as
   theoretical it reads as the recommendation, which it is not; (b) the return leg is drawn by a
   separate, explicitly "illustrative only, not curfew-optimised" function using a fixed
   turnaround assumption, and if that assumption lands inside a restriction it is drawn anyway
   and flagged, on the house rule that an infeasible schedule must never be hidden. Correct by
   that rule, but reads as a bug to a first-time user. Fix is UI labelling plus, ideally, a proper
   search on the return leg. Not a fix to attempt in the pre-holiday window.

6. **Fare as a QSI coefficient.** Wants fare added to the QSI build-up itself, not left as an
   economics-only output. Also raises a separate business/leisure QSI coefficient if Sabre cabin
   split is reliable enough, and an aircraft-type coefficient (787-10 vs A330 perception).

7. **Visual outputs.** More charts, routing maps, interactive hover detail on origin/destination/
   connection points, dynamic behind/beyond routings and volumes on the map.

8. **MCT / terminal override.** Confirm whether the connection builder already reads MCTs and
   terminals by airline/alliance automatically (it does). Wants a manual override exposed so a
   user can test "what if MCT changes here" sensitivities, and similarly wants alliance/codeshare
   membership auto-listed by carrier with the ability to flex it for sensitivity testing.

9. **Aircraft required.** Output the number of aircraft needed to operate the proposed schedule,
   more relevant long-haul.

10. **Pitch generation.** Praised as very useful; expects manual tweaking will still be needed.

11. **CSV/export completeness.** Include the visual outputs and charts in exports, not just data.
    Wants the proposed service shown in the context of the total market: share of the pot captured
    by segment/market, including cannibalisation where relevant.

12. **User/market permissions.** Restrict which markets or datasets a given user can access.

13. **Save/load scenarios.** Downloadable JSON scenario files, re-uploadable later. A comparison
    tab across airlines, frequencies, timings.

14. **Double-stop QSI.** A module for double-connection itineraries; Avia modelled these rarely in
    the past, e.g. for TPE, and he expects it's a relatively easy addition on the existing engine.

15. **Sensitivity / Monte Carlo.** Sensitivity charts or full Monte Carlo, probably on fare and
    frequency or DOC. Notes the departure-time optimiser already does something similar and rates
    it highly.

16. **Fully agentic assistant.** Flagged as the natural next step, no detail given.

Also noted, general: UX described as clean and transparent; comfortable showing the tool at Routes
as a beta even without the visual items above; the CSV reporting and pitch generation both called
out as strong as they stand.
