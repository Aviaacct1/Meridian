# Run sheet: refresh commissioning, watched catch-up to end July

Version 1.0, 16 August 2026. Avia Solutions. Item 8 of HANDOVER-16Aug2026.md.
Run on the WORKSTATION. Companion code: `app/refresh_pickup.py` (built and tested
15 August), `refresh_weekly.ps1` and the portal's `/api/refresh/*` bracket (built
16 August). Everything here is watched: read each output before the next step.

## Pre-flight, once

1. Egnyte drive visible: `dir "Z:\Shared\Company Data\18 Products\QSI\Data Store"`
   shows Jess's regional files. If Z: is not mapped, set AVIA_PICKUP_DIR to the path
   that is.
2. Portal running as normal (Meridian-run.bat). The bracket does not restart it.
3. QSI_PASSWORD visible in the shell that will run the script (`echo %QSI_PASSWORD%`),
   so the wrapper can authenticate to the origin gate.

## Step 1: the plan, and paste it back

    cd C:\src\meridian
    powershell -NoProfile -ExecutionPolicy Bypass -File refresh_weekly.ps1 -PlanOnly

Read the log it names (default E:\Avia\refresh_logs\). What the plan SHOULD show:

- INGEST: the monthly regional files not yet in the manifest, through end July 2026.
  Seven regions per month; a month with fewer than seven wants a question to Jess,
  not a guess.
- HOLD: any 2026 Sabre world file (the vintage guard; a part-year file must never
  advance the base year) and any half-month file (AVIA_BT2_HALFYEAR spine only).
- CONFIRM: complete-year Sabre files, each with its hand-run command printed. These
  never auto-run.
- REFUSE: anything unrecognised. A refusal on one of Jess's real files means the
  tolerance table needs the new spelling, and that is a code change, not a rename
  of her file.

Paste the plan into the chat before executing: that is the watched part.

## Step 2: execute the OAG monthly loads

    powershell -NoProfile -ExecutionPolicy Bypass -File refresh_weekly.ps1

The wrapper brackets the ingest: /api/refresh/begin (portal closes store
connections, /api answers 503 honestly), the loads run one file at a time so a
failure names its file, /api/refresh/end (portal re-opens against the new files;
the end call is in a finally block and cannot be skipped). Then check:

1. The log tail: "N ingested, 0 failed".
2. The Watch page freshness line shows oag_monthly PASS with today's date.
3. One store check, any airport on the dashboard: OAG week label moved as expected.
4. `/api/refresh/state` answers `paused: false`.

A failed file: fix the cause, re-run the same command; the manifest makes the re-run
load only what is missing. A CHANGED historical file is a drop-and-reload decision:
re-run with `--allow-reingest` only after deciding it, per file.

## Step 3: Sabre, by hand if the plan confirms any

Run each printed `sabre_ingest.py` command deliberately, one at a time, inside a
bracket (begin, load, end). Respect the vintage guard: nothing for 2026 until the
year closes. Then `sabre_years.check()` and one dashboard run to confirm the base
year did not move unexpectedly.

## Step 4: register the weekly task

    schtasks /Create /TN "Meridian weekly refresh" /SC WEEKLY /D MON /ST 06:30 ^
      /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\src\meridian\refresh_weekly.ps1"

Run as the logged-on user (E: is a per-logon mapping). The September test is this
task running unwatched, with Jess glancing at the Watch freshness line after each
upload; the verdict is read when John returns.

## What this run sheet does not cover, on purpose

Jess's downloads themselves; the monthly Sabre extraction template (design with
Jess; the vintage guard ships before the first monthly file); the OAG API
(removes the manual step later). Cadence facts in REFRESH-PIPELINE-NOTE-15Aug2026.md.

Avia Solutions Limited. All rights reserved.
