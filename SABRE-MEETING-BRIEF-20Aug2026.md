# Sabre meeting brief: Thursday 20 August 2026, noon

Version 1.0, 19 August 2026. Avia Solutions. INTERNAL WORKING DOCUMENT, John's
speaking notes; not for issue to Sabre. Companion to the compliance audit of
16 August and SABRE-DEMO-WEEK-PLAN-17Aug2026.md.

## Purpose

Demonstrate Meridian to Sabre and secure their written confirmation before World
Routes (21-23 October, Frankfurt). The meeting succeeds if Sabre leaves ready to
confirm the three points below in writing, or names exactly what they need first.

## The three asks

1. **That the named outputs are repackaged analysis under clause 4(b), not
   extracts.** The list: the modelled route forecast and its capture shares; the
   addressable market per route; per-city connecting bases; catchment definitions
   and shares; market fares stated as fixed bands; airport-level demand trends; and
   graded back-test outturns presented as ratios. Every one is computed, none is a
   row of the data.
2. **That the attribution form satisfies the source-statement condition.** The form,
   now on every surface where the data is a material input: "Sabre Global Demand
   Data", with the standard source line "Source: AviaSolutions analysis (Avia
   Cortex); Sabre Global Demand Data; OAG schedules."
3. **That conference demonstration is within the licensed consultancy use**:
   pre-loaded sample markets, exports disabled, a demonstration watermark
   throughout, and no output about an airline visitor's own network.

## Architecture facts to state in support

Data arrives as annual ODPOO files and is loaded offline on one workstation; the
tool holds no Sabre System credentials and makes no connection to Sabre; stores are
opened read-only; no store row reaches any client response; every client-facing
figure is computed; access is a manually curated email list behind Cloudflare
Access with a one-time PIN, plus an origin password on the server itself.

## What changed since the 16 August audit (all live in the build Sabre will see)

The attribution above, replacing five informal variants and five unattributed
surfaces. Measured fares banded on every self-serve surface ($25/$50/$100 fixed
grid; exact figures do not leave the server). Sign-in now enforces the password by
default. Third-party credits corrected (GeoNames, OSM/Carto). One visitor's recent
routes no longer shown to the next. Internal file detail removed from the status
line. Repository hygiene completed 17 August; internal matter, remediated, not
volunteered, counsel's view available if ever needed.

## In progress, said plainly if asked, scheduled before Routes

Per-account query and export logging with daily caps; click-through terms of use
naming the permitted use and the non-airline restriction, with an airline-domain
list that auto-holds registrations and demo requests for a one-tap human release
(the machinery exists and runs the demo-pack quota today); the conference demo mode
itself; deeper rounding of measured bases in payloads. The posture to project:
the audit was ours, the register is worked through in order, and nothing waits on
being asked.

## Demo running order (Teams screen-share from the Dev PC, portal over the tunnel)

1. Sign-in: OTP through Cloudflare Access, then the branded sign-in with the real
   password. The access story told live.
2. Dashboard, the acceptance case: SJC-TPE, CI, A359, 5x weekly. Point out the
   basis line naming Sabre Global Demand Data and the year, the provenance rails
   under the charts, and the fare shown as a band.
3. Methodology page: the proof card and the sourcing note (DOT for US domestic,
   Sabre Global Demand Data elsewhere).
4. Catchment page: the markets table's source line; GeoNames and map credits.
5. Watch page: a US airport, so the demand chart is T-100 and labelled as such;
   the point that every surface names the source that answered.
6. Track record: the whole-engine claims, then ONE airport, US and DB1B-graded.
   Do not open a Sabre-graded airport's per-route table (that presentation moves
   to ratio-and-verdict form under the register; say so if asked).
7. Close on controls: the demo-pack flow's held-pending queue and one-tap release
   as the shape of the extraction controls, then the three asks.

Keep the run to the acceptance route; nothing that computes for minutes over the
tunnel. If a page misbehaves live, say what it would show and move on; the dry run
exists so this does not happen.

## Questions to expect

- Reconstitution: banding and the fixed grid, per-market lists capped, logging and
  caps scheduled, terms of use will prohibit systematic extraction.
- Who can access: named individuals we approve, one by one; no self-serve signup.
- Airlines: clause 4(c) is enforced today by the access list; the airline-domain
  auto-hold adds a systematic check with a human release.
- Where the data lives: one workstation; never in the code repository; no cloud
  copy of the data.
- AI use: the research assistant cites public sources for pitch narrative only;
  Sabre data is never sent to any external service.
- Fares: banded on self-serve surfaces as of this week; exact fares only inside
  Avia-delivered engagement work.

## Logistics, Thursday morning

09:00 workstation pulls and restarts (Workstation Remote block below); confirm
QSI_PASSWORD set and sign-in rejects a wrong password; QSI_DEMO_ENTRY stays unset
(closed) for the meeting. 10:00 dry run on Teams from the Dev PC against
meridian.aviacortex.com, full running order, timings noted. Fix list closed by
11:30 or the affected page drops from the order.

**Workstation Remote**

    cd C:\src\meridian
    git pull

then restart the portal at the machine (Meridian-run.bat) or ask whoever is at the
screen.

Avia Solutions Limited. All rights reserved.
