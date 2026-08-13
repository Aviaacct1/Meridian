# Runbook: 14 August 2026

Version 1.0, written 13 August evening. Avia Solutions. Two objectives, set by John.

Read `bt2/bt2_experiments.log` from the 13 August entries first, most recent last. Read
`RUNBOOK-WIRING-14Aug2026.md` only if the calibrated model comes up; it is not needed for either
objective below and the portal runs on the QSI engine.

---

## Objective 1: the 40-page Observatory deck, generated from any city pair

### What exists

The renderer is built and is not the problem. `deck/` holds `avia_deck.py`, `deck_spec.py`,
`render_pptx.py`, `avia_charts.py`, `avia_maps.py`, `avia_images.py` and `avia_library.py`, plus the
Observatory palette and the brand assets.

The forecast half was joined on 13 August. `app/forecast_to_contract.py` turns a live
`calibrated_forecast` payload into a deck data contract, and `app/deck_from_cases.py` runs a cases
file and writes a contract JSON and workbook per route. It reaches 53 of 56 fields with eight of
nine blocks complete, including the eight-segment table.

`Deck Generator/forecast_spec.py` turns that contract into the forecast section of a deck spec, and
`deck/spec_from_research.py` line 426 is the generic entry point:

    build_spec(research, forecast=None, *, codename, title, strap, prepared_for, ...)

### What is missing, and it is two things rather than one

**The join from a live contract to a rendered deck.** `deck/build_ba_sjc.py` reads a contract and
renders a full deck, so the pattern is proven, but it is bespoke: it names LHR, SJC or British
Airways 57 times and hardcodes its contract path. The generic runner does not exist. That is the
first piece of work and it is a rewrite of `build_ba_sjc.py` against `build_spec`, driven by a
contract path and a research pack rather than by constants.

**A research pack per route.** `build_spec` takes `research` as its first argument.
`deck/research_edi_aus.json` and `deck/research_brs_bos.json` exist and there is nothing for
SJC-TPE. `deck/run_observatory_pitch.py` generates one: `--replay FILE` reads findings from disk and
is free, `--live` calls the AnthropicResearchProvider, needs `ANTHROPIC_API_KEY` and costs circa $4
a run. Its own docstring reports three things that fail silently and should be checked on every run:
keynumbers slides at zero, content slides with no attribution line, and sections with findings but
no prose.

### Imagery

`deck/commons_subjects_sjc.json` shows the pattern: a per-route list of Wikimedia Commons subjects.
`avia_images.py` and `avia_library.py` handle fitting and rights metadata, and `piexif` is in
requirements for exactly that. The imagery library is at `C:\assets` behind `config.ASSETS_DIR`,
102MB for the Observatory set, with a rights manifest.

The rights rule is already settled and must not be re-decided: resolution runs in four tiers and the
use tier is set per engagement, not per image. A panorama licensed for one use is not licensed for
another. See the deck imagery entries in the log.

### Order

1. Generalise `build_ba_sjc.py` into a runner taking a contract path, a research pack and a
   codename. Prove it reproduces the BA deck from the existing contract before pointing it at
   anything new: that is the regression test and it costs nothing.
2. Generate an SJC-TPE research pack, `--replay` first from a hand-written findings file to prove
   the plumbing, then `--live` once.
3. Build the subject list for imagery and run it.

---

## Objective 2: type SJC TPE CI, get the best option, add a curfew, re-optimise

### What exists, and it is most of it

`/api/optimise` already runs frequency across 3, 4, 5, 6, 7, 10 and 14, across carrier types and
seasons, over candidate airlines, and it already takes `curfew_origin`, `curfew_dest`, `partners`
and `forecast_year`. `route_feed.optimise_departure` picks the departure time for the named airline,
with a coarse grid and a refinement, and it honours restricted hours. `aircraft_select` chooses the
gauge and the LOPA.

So the recalculation John describes is largely built. The work is the loop and three corrections.

### The three corrections, in order of how much they change the answer

**The optimiser's objective, and this one is unresolved rather than broken.**
`route_feed.optimise_departure` scores each departure as beyond passengers plus behind passengers,
CONNECTING ONLY. Local demand is not in the objective and neither is yield. On SJC-TPE it therefore
picks 00:30, taking P2P from 83,408 to 55,306 while taking connecting from 31,982 to 96,680. John's
counter is strong and is recorded: it picks 00:30 for China Airlines, 02:00 for EVA and 00:30 for
United against actual SFO departures of 01:05, 01:15 and 23:55, three carriers within 35 minutes, so
on a 13-hour sector local demand is close to time-indifferent and the connecting bank is not.

The test named on 12 August has not been run: re-run the search with a connecting passenger weighted
at 0.7 of a local one and see whether China Airlines still lands on 00:30. Do that before the button
is put in front of a client, because "best option" is defined by this objective.

**The carrier's own seat count in the sweep.** `seats` was added to `/api/forecast` on 13 August and
`/api/optimise` still does not take it. In optimise mode the aircraft is being chosen, so the generic
table is the right answer for a type the carrier does not fly, but where OAG shows the named carrier's own
configuration for a candidate type that figure should be used: China Airlines flies the A350-900 at
306 against the table's 336, and Starlux the same type at 306 against 336. `capacity_frame.frame` is
where those come from.

**The plan cap.** `max_plan_lf` is one global 0.875 applied to every carrier type and haul, and it
can only ever reduce, so it bites hardest on the carriers whose economics depend on filling the
aircraft. It should be per type and per haul from achieved load factors, and the case for it is
measured: the `alt_targets` files written on 13 August give sector outturn over operated seats on
6,478 launches, cuttable by type and haul. That closes LF-CAP-OPEN, which has been open since 12
August.

### What "best" should report

Whatever the loop returns, the page must say which objective produced it and on what basis, the same
way `forecast_engine` and `feed_level` now report themselves in the payload. A recommendation with
no stated objective is the silent-default shape this codebase has been caught by twelve times in one
day.

---

## Two things carried from 13 August that neither objective should disturb

The connecting feed runs at `qsi_k` 1.0 and RECUT-RESULT measured it over-reading actual connecting
traffic by circa ten times on the median back-test route. It is exposed as a parameter and defaults
to the shipped value, so nothing has moved, but the optimiser's objective is built on connecting
passengers and the two questions meet.

The half-year OAG union is built and off behind `AVIA_BT2_HALFYEAR`. It changes `capa`, `qcx` and
`legs_n` for cohorts 2016 and 2017 and needs a capture rebuild and a re-measure. Do not combine it
with either objective.

Avia Solutions Limited. All rights reserved.
