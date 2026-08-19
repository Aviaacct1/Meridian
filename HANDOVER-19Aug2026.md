# HANDOVER - 19 August 2026, afternoon session close

Written by the Cowork session that ran 16-19 August 2026 (item 7 build through the
Sabre compliance week and the SJC-TPE pitch). This file is the pickup point for the
next chat. Read it top to bottom before doing anything, alongside the memory index
(MEMORY.md), whose READ-FIRST files are `meridian-acceptance-close-15aug`,
`meridian-pack-maps-16aug`, `meridian-download-fidelity`, `qsi-oag-coverage-aug26`
and `meridian-sabre-compliance-audit`. This handover holds the state of THIS moment;
memory holds the standing knowledge. Where they differ, this file is newer.

The pickup prompt for the new chat is at the bottom.

---

## 1. The clock

- **Sabre demo: Thursday 20 August, noon**, Teams screen-share from the Dev PC.
  John gives Sabre no access of any kind. Running order and checks in
  `C:\AviaDev\SABRE-MEETING-BRIEF-20Aug2026.md`.
- **Dry run: today (Wednesday 19 August) at 16:00.** Checks: acceptance figure
  131,812 at 2026, a download smoke test, a fresh OTP through the Cloudflare email
  policy. `WARM-PAIRS.ps1` (C:\AviaDev root) warms the pitch pairs first.
- John-side today: the aviationobservatory.com domain and mailbox, then
  `setx AVIA_SMTP_USER` / `AVIA_SMTP_PASS` on the workstation (unblocks the live
  demo-pack email send, item 10); his "item 6" from his own list.

## 2. State of play at session close (19 August, afternoon)

**Repo.** github.com/Aviaacct1/Meridian (private). Tip on main, both machines:
`6e80045  Pitch cases: the three recommended 5x runs (CI A359, BR B77W, JX A359)
at the 20:59 evening wave, engine-default growth, shipped floor`. Workstation
`git pull` confirmed "Already up to date" at 6e80045 this afternoon, so all code
including the Departure curve sheet is ON the workstation disk.

**The one open fault: the portal process is stale.** The running Meridian portal on
the workstation predates the curve-sheet commit, which is why the three re-downloaded
5x files, Meridian_SJC_TPE (7)(8)(9).xlsx, still lack the Departure curve sheet.
The fix is not a pull; it is: close the Meridian console window (actually end the
process), then run `Meridian-run.bat` fresh. Running the bat over a live server only
re-warms the old process (the known trap, hit twice this week).

**The three 5x downloads verify.** (7) JX A359 306 seats, LF 0.824, total 65,593
each way. (8) CI A359 306, LF 0.875, 69,615. (9) BR B77W 333, LF 0.826, 71,511.
All three match the recommended cases digit for digit. Source: the three xlsx files
John downloaded 19 August; the totals also appear in `cases_sjc_tpe_pitch.json`'s
note. They only lack the curve sheet.

**deck_from_cases ran clean on the workstation.** Three cases, 53 of 57 fields
(93%) each, qsi engine, contracts written to `E:\Avia\contracts`. Env vars used:
`AVIA_FREQ_SENSITIVE=1`, `AVIA_SABRE=E:\Avia\sabre.duckdb`,
`AVIA_OAG=E:\Avia\oag.duckdb`.

**Two of three packs built.** `SJC-TPE_ChinaAirlines_pack.pptx` and
`SJC-TPE_EVAAir_pack.pptx` in `E:\Avia\contracts`, 15 pages each, content budget
clean, cover hero resolved from the brand library. Two slides DROPPED by design:
competition (waits on Job 3, per memory `meridian-pack-maps-16aug`) and
this-forecast-against-the-last (no prior forecast exists; the slide drops, per the
download-fidelity ruling).

**The third pack FAILED on a filename, not on substance.** The JX case is named
`PITCH SJC-TPE JX A359 306 5x 2027 Starlux`, so its contract file carries
`_Starlux` at the end: `PITCH_SJC-TPE_JX_A359_306_5x_2027_Starlux_contract.json`.
The command block issued at session close (section 3) uses the corrected name.
Not yet confirmed run.

**Pitch cases file.** `app/cases_sjc_tpe_pitch.json`, committed at 6e80045.
Defaults: SJC-TPE, FSC, split_floor true, dep_time 20:59 (fixed, because the cases
runner has no curfew field and 20:59 is what the optimiser chose under John's
21:00-06:00 curfew scenario), forecast_year 2027, season annual. Growth is the
engine default (measured pre-COVID trend, +18.3% to 2027 on this pair). Cases:
CI A359 306 5x, BR B77W 333 5x, JX A359 306 5x.

## 3. The blocks issued and not yet confirmed run

These were the last thing given to John. The new chat should ask whether they ran
and pick up from the transcripts he pastes.

**Workstation Remote** (finish the third pack)

```powershell
cd C:\src\meridian\deck
dir E:\Avia\contracts\PITCH*.json
py -3.12 forecast_pack.py "E:\Avia\contracts\PITCH_SJC-TPE_JX_A359_306_5x_2027_Starlux_contract.json" --out E:\Avia\contracts\SJC-TPE_Starlux_pack.pptx --codename "Meridian" --prepared-for "STARLUX"
```

**Workstation Actual** (restart the portal onto current code; close the Meridian
console window first, actually end it)

```powershell
cd C:\src\meridian
.\Meridian-run.bat
```

Then hard-refresh the dashboard and re-download the three 5x runs; the Departure
curve sheet appears in each.

**DevPC** (bring packs and contracts back for QA; scp to a Windows remote takes no
globs, name every file)

```powershell
cd C:\Avia_extracts
scp aviaremote1@donatello:"E:/Avia/contracts/SJC-TPE_ChinaAirlines_pack.pptx" .
scp aviaremote1@donatello:"E:/Avia/contracts/SJC-TPE_EVAAir_pack.pptx" .
scp aviaremote1@donatello:"E:/Avia/contracts/SJC-TPE_Starlux_pack.pptx" .
scp aviaremote1@donatello:"E:/Avia/contracts/PITCH_SJC-TPE_CI_A359_306_5x_2027_contract.json" .
scp aviaremote1@donatello:"E:/Avia/contracts/PITCH_SJC-TPE_BR_B77W_333_5x_2027_contract.json" .
scp aviaremote1@donatello:"E:/Avia/contracts/PITCH_SJC-TPE_JX_A359_306_5x_2027_Starlux_contract.json" .
```

## 4. QA owed by the assistant once files arrive

1. **Contracts**: verify the three totals reproduce the recommended runs digit for
   digit: CI 69,615 / BR 71,511 / JX 65,593 each way. If a contract diverges from
   its download, stop and diagnose before any pack is shown; the one-run-definition
   only covers the portal path, and deck_from_cases is a separate entry point that
   must be proven to agree.
2. **Packs**: page-by-page review of all three pptx (naming: Meridian analysis /
   The Aviation Observatory, never Avia Cortex, never Avia Solutions analysis;
   source line on every figure; fare as band not exact; airline name resolved, never
   "Generic (airline-agnostic)"; chart units and periods labelled; en/em-dash sweep;
   en-GB proofing on anything Word/PowerPoint we generate ourselves; pack pages come
   from the product renderer so review, do not silently edit).
3. **Curve-sheet downloads**: confirm the Departure curve sheet is present, the
   curve reconciles with the headline at 20:59 (chosen-departure row equals
   connecting_carried x2 and total x2), permitted flags carried, native chart
   embedded. The offline test already proves the code path
   (`app/test_workbook_table.py`, 15 checks including the curve block).

## 5. The timing slides (blocked on the curve downloads)

John said "yes please do" to timing slides with each airline's own departure curve.
Plan: three slides appended to the delivered table deck, taking it 6 to 9 slides.
Per slide: that airline's curve from its xlsx Departure curve sheet (local,
connecting shown uncapped, capacity ceiling, total two-way), the chosen 20:59
marked, a short note on why the evening wave lands TPE in a different connecting
bank from that carrier's own SFO night service. Build with the same pptxgenjs
generator pattern as the table deck (NAVY 1F3864, the /tmp/decks.js conventions;
regenerate, /tmp does not persist across sessions). Caveat that stays on the deck
until confirmed: the curfew hours used are John's 21:00-06:00 scenario; confirm
SJC's actual curfew before client use.

**The delivered deck**: `SJC-TPE airline forecast tables - 19Aug2026.pptx` in the
project folder (OneDrive "Avia QSI Tool"). Six slides: optimised bases plus
comparable 5x bases (John's answer: "Both").

## 6. The airline recommendations (decided, 19 August)

- **China Airlines**: show the 5x A359 306. 69,615 each way at the 87.5% cap.
  Story: continuity and growth on last year's pitch (which was 4x at 86.4%);
  the route is capacity-bound, the demand is there.
- **EVA Air**: show the 5x B77W 333. 71,511 at 82.6%. Story: SJC complements SFO;
  the workbook sub-rows answer the cannibalisation question with numbers.
- **STARLUX**: show the 5x A359 306. 65,593 at 82.4%. Story: the entrant's route;
  no self-competition question to answer.
- All three: evening ~20:59 departure under the 21:00-06:00 scenario, arriving TPE
  in a different bank from the SFO redeyes, so the SJC service adds connecting
  windows rather than cannibalising them.

## 7. Machines, paths, conventions (operational summary; detail in memory)

- **Command block convention (non-negotiable)**: every block is labelled DevPC /
  Workstation Remote / Workstation Actual, opens with the cd, one machine per
  block, commands only. John pastes transcripts back; read them fully, they are
  the ground truth.
- **DevPC clone**: `C:\AviaDev` (app/, deck/). This is also where handovers,
  runbooks, briefs and COMMIT-MSG-*.txt live. The Cowork mount of it denies
  delete/overwrite for git purposes: **never run git against the mount**; write
  code with the file tools, give John the commit block, he runs it.
- **Workstation (donatello)**: clone `C:\src\meridian`, data on `E:\Avia`
  (sabre.duckdb 286.5m rows, oag.duckdb 210.8m rows), contracts
  `E:\Avia\contracts`, portal via `Meridian-run.bat`. Remote route: ssh as
  aviaremote1 (Tailscale); RDP evicts whoever is at the screen. Z: (Egnyte) is
  per-logon and invisible in ssh sessions.
- **scp transfer point on DevPC**: `C:\Avia_extracts`. SHA256 both ends when it
  matters.
- **Cloudflare**: meridian/atlas live at aviacortex.com behind email policy + OTP;
  100-second rule is why /api/report and /api/optimise are background jobs;
  /api/forecast is the remaining watch item.
- **File uploads**: xlsx files John downloads land in the chat; verify them with
  openpyxl in the sandbox (mounts: outputs, AviaDev, the project folder).

## 8. Traps that burnt us this week (do not relearn these)

1. Meridian-run.bat over a live server re-warms the old process. Kill the window
   first. Stale dashboard HTML compounds it; HTML now ships Cache-Control:
   no-cache, but the server process itself must be restarted.
2. John pasting prose into PowerShell caused a junk commit and a force-push
   recovery. Hence the command block convention. Blocks contain commands only.
3. The report-drift trilogy ended with the real cause: the server never resolved
   carrier-config seats until the explicit default was added to api_forecast
   (`config_for(airline, gcd_km)`); it lives ONLY there, not in
   calibrated_forecast, which is why cases files pass seats explicitly.
4. Downloads must never silently fall back: lastQ is the run on screen, optimise
   seeds it from the result picks, refusal scrolls into view. If a download
   refuses, the cause is a stale page or a cleared run, not the engine.
5. "Flat shares cv 0.000" was an assistant bug (contract vs payload key names),
   corrected on the record. When a validation harness reads two sources, it reads
   both key vocabularies or refuses; it never defaults.
6. scp to the Windows workstation: no wildcards, name each file.
7. The seat placeholder sticking at the previous airline's config: fixed with
   resetSeatHint on airline/aircraft change; if seen again it is a stale page.

## 9. Standing rulings in force

- **Naming**: product is Meridian, published by The Aviation Observatory. Client
  surfaces say "Meridian analysis, The Aviation Observatory". The source line as
  built is BLESSED for year one (brand building); only revisit if it grows crazy
  long. Avia Cortex was a dev name; it appears nowhere client-facing. Filenames
  Meridian_*.
- **Sabre compliance**: attribution is the single constant in app/attribution.py
  ("Sabre Global Demand Data"); fares leave the server as bands only (fixed grid,
  app/fare_bands.py); Sabre-graded track-record rows show size band + ratio +
  verdict, never volumes; single-route blind figures are never client-facing.
  Demo-critical register items R1, R3, R4, R5, R8, R12, R13, R16, R19, R24 are
  CLOSED. Gap register in the project folder; week plan and R1 purge runbook in
  C:\AviaDev.
- **Download fidelity**: a download reproduces THE RUN ON SCREEN. api_report calls
  api_forecast; by construction they cannot differ. Any new output path must join
  that one-run-definition (pitch-job alignment is on the post-Sabre queue).
- **One Meridian model**: one engine, 60% by route, 86/92 grouped. Never a second
  engine, never lower the claims.

## 10. Post-Sabre queue (nothing here before Thursday)

R6/R7 depth; R9 per-account query log (converges with the usage-data asset,
memory `meridian-usage-data-asset`); R17 ToU incl. banking analytics consent; R18
demo mode; pitch-job one-run alignment; portal as a Windows service; catchment map
restyle (Leaflet banded-dot into avia_maps); /api/forecast job-pattern watch item;
fleet delivery layer (memory `meridian-fleet-delivery-layer`; interim rule: manual
gauge+seats, "seats: caller"); confirm SJC's actual curfew hours; appendix 4x/2028
variants if wanted; Sabre confirmation letter after the meeting; OAG letter after
the new OAG agreement arrives (John is waiting on it); radar loader lift from
/signin (design found there, not lost).

## 11. Key files, one line each

- `C:\AviaDev\SABRE-MEETING-BRIEF-20Aug2026.md` - Thursday's running order.
- `C:\AviaDev\SABRE-DEMO-WEEK-PLAN-17Aug2026.md` - the week plan, R-item map.
- `C:\AviaDev\SABRE-R1-PURGE-RUNBOOK-17Aug2026.md` - executed; waypoint tagged.
- `C:\AviaDev\RUNSHEET-refresh-commissioning-16Aug2026.md` + `refresh_weekly.ps1`
  - refresh wiring; the watched catch-up run is John's, needs the session with Z:.
- `C:\AviaDev\HANDOVER-16Aug2026.md` - the previous handover (items 7-10 era).
- `C:\AviaDev\app\cases_sjc_tpe_pitch.json` - the three pitch cases.
- `C:\AviaDev\app\test_workbook_table.py` - 15 checks incl. the curve sheet.
- Project folder: `SJC-TPE airline forecast tables - 19Aug2026.pptx` (delivered),
  `EVA-deck-fill-review-18Aug2026.md`, the Sabre gap register, `contracts\`.
- `NOTE-Atlas-QSI-current-method-16Aug2026.md` (C:\AviaDev) - the Atlas note, sent.

---

## 12. Pickup prompt for the new chat

Paste this as the first message:

> Continue the Meridian work. Read, in order: (1) your memory index MEMORY.md and
> its READ-FIRST files, (2) C:\AviaDev\HANDOVER-19Aug2026.md, which is the state
> of play and is newer than memory where they differ. Then confirm back to me in a
> few lines: what the Thursday deadline is, the three airline numbers, and the
> three actions in flight (JX pack build, portal restart for the curve sheets,
> scp of packs and contracts for QA). Do not rebuild anything that the handover
> says is built; verify instead. I will paste transcripts of the blocks I have
> run and upload the re-downloaded xlsx files; pick up from there. Rules that
> hold: command blocks labelled DevPC / Workstation Remote / Workstation Actual
> with the cd first and commands only; never run git against the mounted repo;
> one Meridian model; a download reproduces the run on screen.

---
*Avia Solutions internal. 19 August 2026. Session handover, supersedes nothing,
complements HANDOVER-16Aug2026.md and the memory store.*
