# HANDOVER - 23 August 2026: pre-holiday readiness push

Written by the Cowork session that ran through 22-23 August 2026 (the EW/2-way workbook
feature, the domestic/international basis convention in deck_contract.py, three PDEW/PTEW
basis bugs, the "0 finds" research fix, and the labelling gaps in pitch_html.py and
route_deck.py). This file is the pickup point for the next chat, and it carries a
different kind of instruction from the usual: John leaves for holiday in three days
(by roughly 26 August) and wants Meridian - and separately, Atlas - in a state where a
team of testers can use the products unsupervised while he's away, so he comes back to a
genuine list of findings rather than a list of things that were already known and broken.

Read this file top to bottom before doing anything. Read the memory index (MEMORY.md) and
its READ-FIRST files alongside it, in particular `meridian-acceptance-close-15aug` and
`meridian-pack-maps-16aug`. Where this file and memory differ, this file is newer.
`HANDOVER-19Aug2026.md` is the previous handover (Sabre demo week); nothing in it is
superseded by this one except where explicitly noted below - the Sabre demo happened on
20 August and this file does not know how it went, see section 3.

**The task for today is section 4, in order.** It is a punch list, not a design problem:
deploy what is already built, verify it live, close two loose ends from today, run one
clean regression baseline, provision tester access, and triage the one UX risk most likely
to generate false bug reports while John is away. Nothing in section 4 requires new
design decisions. Where a step needs a decision only John can make, it says so and stops
there rather than guessing.

**ADDENDUM, added after this handover was first written today, now CLOSED**: a fifth
instance of the PTEW basis bug was found and fixed after section 3 below was written, and
it was confirmed to be the actual cause of Jol Kingham's "PTEW mismatch" email of 22
August. Task 0 in section 4 (below) covers the full story: the fix alone did not show up
in the first regeneration, because the live server process had not been restarted, only
pulled - proof, live, of the standing "a pull does not update an already-running process"
trap. After a proper restart, all three CI/BR/JX workbooks checked out clean and John has
sent the corrected files to Jol. No action needed on this by whoever picks this file up
next; it is recorded here for the record, not as a task.

**SECOND ADDENDUM, 24 August 2026, CODE DONE, LIVE VERIFICATION AND SEND STILL OWED**: Jol
sent a follow-up email the same morning, this time on labelling and display precision in
the corrected CI/BR/JX workbooks (the underlying PTEW figures themselves were already
right - see above). Six fixes made in `app/cortex_workbook.py`, all traced against the
code's own logic before being made, not guessed: Cover tab's PTEW row spelled out in full
("Passenger Trip Each Way (PTEW)", John's own wording); Cover tab now carries 2-way
figures alongside each-way for the four forecast rows; the "2,025" year-formatting bug
fixed (was falling into the generic thousands-separator format); "OAG schedule week"
relabelled "(beginning)", sourced from `resolve_oag_week()`'s own docstring ("week
commencing"); Forecast tab demand/forecast columns bumped from 1dp to 3dp; Connecting feed
header row renamed "Airport Code"/"City Name"/"Country Code", traced against
`_feed_list()`'s actual field semantics. Full detail and verification in
`COMMIT-MSG-24Aug2026-jol-second-email-cover-forecast-feed-labels.txt`. `test_workbook_table.py`
passes 23/23 (its Cover-PTEW-lookup updated to the new label) and a dedicated sweep of
`app/` found no other code or test depending on the six changed strings/formats/row-counts.
Full regression suite run clean bar two pre-existing sandbox-only failures (no `fastapi`
installed; a workstation-only `Z:` drive reference file), neither touching this change.

**Not done**: no live regeneration of a real route workbook against these code changes -
that needs the workstation, same as the first PTEW fix, which looked right in the sandbox
too until a live regeneration caught the stale-process trap. **Do not send anything to Jol
until a workstation-regenerated CI/BR/JX (or equivalent) file has been eyeballed against
this list.** Files changed and staged for commit, not yet committed or pushed - see the
DevPC block in that COMMIT-MSG file's own session for the exact `git add` list (deliberately
excludes three xlsx/pptx test-output files this session's own local test run touched as a
side effect, and the pre-existing unrelated `diag_tpe_sjc_catchment_decomp.py` edit).

**THIRD ADDENDUM, 24 August 2026, same day, CODE DONE, LIVE VERIFICATION AND SEND STILL
OWED**: Jol sent a further follow-up within the hour (12:27) - the labelling batch above
did not touch the actual PTEW figures, and he had already spotted they were still wrong:
"unless I am going mad... does not match Cover tab row 24, nor the two Forecast tabs...
the two forecast tabs PTEW sum of parts (267) does not match the total (268)." Two real
issues found and fixed in `cortex_workbook.py`, not display bugs this time. First: the
Forecast tabs' GRAND TOTAL PTEW was independently rounded from the true total rather than
summed from the three displayed rows, so 267 (sum of the rounded parts) and 268 (round of
the true total) were both "correct" and never going to agree by hand - now the GRAND TOTAL
row sums the displayed parts, so it foots exactly, always. Second: the Connecting feed
tabs had no Total row PTEW figure at all (Jol was summing city rows himself), and the
All-other row's own PTEW used a flat weeks-times-7 denominator (assumed daily service) -
the SEVENTH instance of this week's flat-day PTEW bug, found only because this fix went
looking for why the tab had no total to check against. Both fixed; full detail in
`COMMIT-MSG-24Aug2026-jol-third-email-ptew-footing-and-feed-total.txt`. Two new regression
checks added (GRAND TOTAL footing is now a hard equality, not a tolerance); 26/26 checks
pass; full suite re-run clean bar the same two pre-existing sandbox-only failures. **Not
done: live regeneration and eyeball check against a real CI/BR/JX file - do not send
anything further to Jol until that is done.** This is now the THIRD time this week a
sandbox-verified PTEW fix has needed a live check before being trusted; treat that as the
standing rule for this figure specifically, not bad luck.

**FOURTH ADDENDUM, 24 August 2026, same day**: the labelling batch's live check (finally
run against a genuinely fresh workstation build, after an unrelated detour - see below)
confirmed the Cover, footing and Connecting feed Total fixes all work correctly, but
caught a real miss: the Forecast tabs' demand columns showed "160.900" instead of real
3dp precision. The number FORMAT string had been changed correctly, but the underlying
`k()` rounding lambda was still baked to 1dp before the format ever saw it - value and
format changed independently, only one of them got fixed. Corrected (1dp to 3dp);
`COMMIT-MSG-24Aug2026-forecast-tab-3dp-precision-fix.txt` has detail. Also recorded here
because it is a genuinely useful lesson for future work on this file: a display FORMAT
change and a VALUE rounding change are two different things, and checking only the format
string is not enough - the sandbox test suite's loose tolerances did not catch this either,
only John's own eyeball check of a live file did. **Separately, and not a code issue**:
today's push took three attempts because `C:\AviaDev` and `C:\src\meridian` are two
separate clones of the same repo on John's machine, and a stale `.git\index.lock` in
`C:\AviaDev` (left by this session's own read-only git calls through the Cowork mount)
blocked commits there until manually removed. Both clones are now in sync at the latest
commit; worth a decision at some point on whether to keep running two clones.

**FIFTH ADDENDUM, 24 August 2026, CLOSED, verified against a live regeneration**: a fresh
CI workbook, regenerated on the workstation after the 3dp fix, checked out correct against
every point in both of Jol's emails - the PTEW label spelled out in full, the Cover 2-way
rows (exact doubles, cross-checking against the Forecast tab's carried legs to the pound),
the year printing clean with no comma, the OAG week reading "(beginning)", the Forecast
tab's genuine 3dp precision, the GRAND TOTAL PTEW footing exactly (120 + 36 + 112 = 268 on
both EW and 2-way), the Connecting feed headers renamed, and the Connecting feed Total row
now printing a real PTEW figure consistent with the Forecast tab's own leg figure. Ready to
send to Jol. No action needed by whoever picks this file up next.

**SIXTH ADDENDUM, 24 August 2026, same day, CODE DONE, LIVE VERIFICATION AND SEND STILL
OWED**: the "ready to send" verdict above was premature - Jol sent an annotated screenshot
minutes later showing his own working: "the PTEW column in the excels don't add - CI says
268 but is 270 sum of the parts, same for the others." He was summing one level deeper
than what got fixed earlier - the Forecast tab's competition sub-rows (not the leg-total
rows above them) and the Connecting feed tabs' individual city rows plus All-other - and
each of those, being independently rounded, drifted from its own parent total by ordinary
rounding error, the same pattern as the earlier fix just recurring one level down. Fixed
with the same principle: the smaller/residual item in each breakdown (the "without direct
competition" sub-row; the "All other" row) is now the remainder against its own parent
total rather than an independent rounding, so every level of both tables foots exactly,
not just the top. Full detail in
`COMMIT-MSG-24Aug2026-ptew-footing-one-level-deeper.txt`. Two new regression fixtures
added (30/30 pass, up from 26), one of which needed real competition_split data added to
the test fixture since the sub-row code path had never actually been exercised by a test
before. **Not done: live regeneration and an eyeball check against Jol's own annotated
numbers - do not send anything further to him until that is done.** This is now the fourth
distinct PTEW-related fix this week that has needed a live check; the pattern is clearly
"verify every PTEW change against a live file before saying it's ready," not bad luck.

**CLOSED, verified against a live regeneration**: a fresh CI workbook checked out exactly
against Jol's own annotated screenshot numbers - Forecast sub-rows now foot 2+34=36 (was
2+33=35) and 36+76=112; Connecting feed SJC behind foots 33.9+1.7=35.6 (All-other moved
1.6->1.7); TPE beyond foots 93.5+18.3=111.8 (All-other moved 18.2->18.3). GRAND TOTAL
120+36+112=268, matching on both EW and 2-way tabs. Ready to send to Jol. No action
needed by whoever picks this file up next.

---

## 1. The clock

- **John leaves for holiday in three days** (from 23 August - so by roughly 26 August).
  No fixed hour is recorded; treat "before he leaves" as end of day 25 August to leave a
  buffer.
- **No World Routes booking decision to action.** John is deliberately not booking World
  Routes yet - he is waiting on client payments and cannot currently afford the circa
  £20,000 the booking needs. This is a business decision he has already made, not a task;
  do not chase it, do not raise it unless he raises it first.
- **A separate, dated item that sits right on top of his departure:** the Atlas note
  (`C:\AviaDev\NOTE-Atlas-QSI-current-method-16Aug2026.md`, section 4 item 4) says the
  accuracy-claim wording decision must go to John "before 26 August with both texts in
  front of him." That is a different repo and a different chat (the Atlas build chat, not
  this one), so this session has no visibility into whether it has already happened. See
  section 4, task 8: the action here is to ask John directly, not to guess or to try to
  reach into the Atlas repo from this session.

## 2. What "ready for testers" means here

Not a new feature push. It means: the code that exists and has been fixed over the last
four days is actually running on the machine testers will use, the two things fixed today
that could not be verified live in this session are now confirmed live, there is one clean
regression baseline dated today, testers can actually get through the login gate, and they
are handed a short list of what is already known so their week doesn't just rediscover the
backlog. Section 4 is that list, nothing more.

## 3. State of play at session close (23 August, morning)

**Repo.** `C:\AviaDev`, github.com/Aviaacct1/Meridian (private). Confirmed this session:
`git rev-parse HEAD` and `git rev-parse origin/main` are IDENTICAL
(`5edb8d369e0d4eaae28d71b7a214de55a5476f20`). Nothing is committed-but-unpushed. Last 8
commits, newest first:

```
5edb8d3  Task 60: wire the basis label into route_deck.py, using its own existing pattern
1d0444d  Fix the researched-pitch "0 finds" and label the digital pitch HTML's basis and vintage
14be703  Fix /api/pitch/health has_key to reflect the loaded key, not just the env var
0c4e730  US domestic routes state passenger counts each way, international stays two way
4b4aff4  Three more each-way/departures basis bugs, found checking for domestic/international logic
5aa8ebd  Fix test_workbook_table.py for EW/2-way tab names, 22/22 checks pass
2ab470e  Fix EW/2-way check script: read both title rows, not just row 1
bf818a1  Workbook tabs carry EW / 2-way pairs, so the basis is in the tab name
```

**What these commits actually did, in plain terms** (full detail in the matching
`COMMIT-MSG-*.txt` files at repo root, see section 7):

1. **cortex_workbook.py**: every downloadable Excel sheet that carries a passenger count
   (Forecast, Connecting feed, Schedule, Departure curve, Catchment, Competition) now
   builds as a PAIR of tabs, one suffixed "EW" (each way) and one "2-way", computed once
   each-way and doubled only at the point figures are written to cells. Economics stays a
   single tab (costs and seats don't have a coherent each-way half), retitled to state
   "two way" explicitly. Verified 22/22 on `test_workbook_table.py`.
2. **deck_contract.py**: three separate instances of the same bug class fixed - PDEW/PTEW
   was dividing by a flat 728 (or 365) departures assumption regardless of the route's real
   frequency, in `deck_contract.py`'s own `pdew()`, in `forecast_to_contract.py`'s
   duplicate fallback, and in `route_deck.py`'s reconstruction of an annual figure from an
   already-correct rate. A second, independent bug: the per-city connecting tables
   (`connecting_at_hub`/`connecting_at_destination`) were never doubled, so they read at
   roughly half of the same contract's own summary total for the same market.
3. **The domestic/international convention** (the main piece of design work this week):
   US-domestic routes now display passenger counts each way (the DOT/T-100 convention);
   everything else, SJC-TPE included, stays two way. `case["domestic"]` is set once, in
   `forecast_to_contract.case_and_outputs()`, from both endpoints' country codes. Every
   number in `build_contract()` is still computed two way exactly as before; a new
   `_disp()` wrapper halves ONLY the specific passenger-count summary fields for a domestic
   route, at the point they're written into the contract - never capacity, schedule,
   revenue, yield or fares, which are operational/financial facts, not a passenger-count
   convention. `contract["_demand_basis"]` states which basis is in force, plus a `_basis`
   note repeated on every block that carries a `_disp()`'d figure. Verified 27/27 on
   `test_deck_contract_ptew.py`; the BA LHR-SJC 2015 acceptance fixture rebuilt
   byte-identical (82,708 P2P forecast, PDEW 113.6), so nothing already shipped moved.
4. **research_provider.py**: `DEFAULT_MODEL` was `"claude-sonnet-4-6"`, which is not and
   has never been a real Anthropic model ID (checked against a live model list this
   session: current IDs are claude-fable-5, claude-opus-5, claude-sonnet-5,
   claude-haiku-4-5-20251001). Every `research_block()` call was throwing at
   `client.messages.create()`, caught silently, returning zero findings per block - this
   is almost certainly the literal cause of John's "0 finds" report today. Fixed to
   default to `"claude-sonnet-5"`. **Not yet confirmed against the live API from any
   session** - the sandbox this work was done in has no key. Task 2 below closes this.
5. **pitch_html.py**: the digital HTML pitch pack (the file John uploaded as
   `Meridian_Pitch_SJC_TPE_JX_5x.html`) had base year, forecast year and the growth basis
   already present in its own embedded data and never rendered anywhere on the page. Added
   a document-level basis/vintage line plus a labelled note above each of the four
   sections John named (traffic forecast, connecting markets, schedule and capacity, route
   economics), including an explicit fix for the schedule table, which mixed each-way
   per-direction rows and a two-way Total row with nothing on the table saying so. Missing
   years read "not stated", never silently omitted. Verified against two synthetic
   fixtures, executed headlessly in Node/jsdom, no script errors either way.
6. **route_deck.py**: confirmed LIVE this session (called directly from `cortex_app.py`'s
   deck-download endpoint, both the `app/` and `app_avia_style/` copies) - this resolves
   the "unconfirmed whether it's even the live path" note from earlier in the week. Its own
   pre-existing pattern ("X each way, Y both ways/yr") already covered two of its four
   headline stats; extended to all four, plus the five-year build table and the connecting
   feed detail table, which had no basis stated at all. Verified by building a full
   seven-slide synthetic deck and rendering it to PNG via LibreOffice; no text overflow in
   the tightened header cells.
7. **cortex_app.py** (both copies, a known duplicate-file gap not fixed here): `has_key` in
   `/api/pitch/health` now reads the provider's actually-loaded key
   (`getattr(prov, "_key", "")`), not just the env var, so it stops misreporting `false`
   when the key was found via the gitignored `anthropic_key.txt` file fallback. Also
   carries `captured_2w`/`feed_2w`, needed for task 6's route_deck.py fix.

**What this session does NOT know, and the next chat must find out, not assume:**

- **Whether the workstation (donatello, `C:\src\meridian`) has pulled any of this.** This
  session has no access to that machine. Section 4 task 1.
- **How the Sabre demo on 20 August went.** No post-demo note exists anywhere in the repo
  or in memory. Not this session's business to guess at - if it's relevant to today's
  readiness push, ask John, don't infer from silence.
- **Whether the Anthropic key fragment exposed in a PowerShell paste earlier this week has
  been rotated.** Flagged at the time; no confirmation seen since. Section 4 task 3.
- **The current git status has some loose ends, none of them from today's work**: `git
  status --short` shows `diag_tpe_sjc_catchment_decomp.py` modified (pre-existing, not
  touched this session) and four untracked `COMMIT-MSG-*.txt` files from 20-21 August that
  were apparently drafted but never committed alongside their code
  (`COMMIT-MSG-20Aug2026-connecting-basis-fix.txt`,
  `COMMIT-MSG-20Aug2026-connecting-city-table-halving.txt`,
  `COMMIT-MSG-21Aug2026-p2p-connecting-split-check.txt`,
  `COMMIT-MSG-22Aug2026-deck-contract-basis-fixes.txt` - the last one's actual commit did
  land, at `4b4aff4`, just without this file riding alongside it). Harmless, but worth a
  tidy commit if there's a spare five minutes; not blocking.
- **`git status` on this mount throws `unable to unlink '.git/index.lock': Operation not
  permitted`** even for a read-only status check. It didn't corrupt anything - the read
  still completed - but it's a live confirmation of the standing rule
  (`cowork-mount-permissions` memory): never run `git commit` or `git push` against this
  mount. Read commands appear tolerant of the failed lock cleanup; write commands are not
  worth testing to find out.

## 4. TODAY'S PUNCH LIST

Work through these in order. Each has a command block (labelled DevPC / Workstation Remote
/ Workstation Actual per the standing convention - one machine per block, commands only,
John pastes the transcript back) and an explicit pass/fail so there's no ambiguity about
whether a step succeeded.

### Task 0 - CLOSED (23 August, same day). Regenerate and send the corrected CI/BR/JX workbooks to Jol

Found after the rest of this handover was written, so it sits out of numerical order but
not out of priority: Jol Kingham (22 August, "SJC: PTEW mismatch" and its follow-up)
reported that Cover, Connecting feed and Forecast showed three different PTEW figures for
the same route, and separately asked that the model say "PTEW" everywhere, never "PDEW".
Three earlier fixes this week addressed the same bug CLASS in four other places, but not
the actual cause: `cortex_app.py`'s own `pdew_total` (both the `app/` and
`app_avia_style/` copies) - the figure Cover prints verbatim - was dividing by a flat 365
regardless of frequency, while the Forecast tab was already dividing by the route's real
freq x weeks. On CI/BR/JX, all 5x/week, that's 365 versus 260 departures a year, a circa
40% gap between two tabs of the same workbook. Fixed; a new regression check in
`test_workbook_table.py` (23/23 passing) now asserts Cover and Forecast agree, so this
can't silently reopen. Full detail:
`C:\AviaDev\COMMIT-MSG-23Aug2026-jol-ptew-mismatch-root-cause.txt`. Also swept: two
remaining live "PDEW" labels in `pitch_html.py` and two in `deck/forecast_spec.py`
(confirmed live via `pitch_report.py`), plus a sixth instance of the same flat-day bug in
`forecast_spec.py`'s `_fc_connecting`. `deck/build_ba_sjc.py`'s three PDEW headers were
deliberately left alone - the frozen "Project Redwood" historical BA deck, same category
as the `ba_lhr_sjc_reference()` fixture.

**DONE.** The first regeneration (still on the pre-restart server process) reproduced the
exact same 1.40x mismatch (365 vs 260 departures/year), proving the code fix alone is not
enough - the live server process has to be actually killed and restarted, a pull does not
touch an already-running process. After `Meridian-run.bat` was properly restarted (window
closed first, not just re-run over the live one), all three regenerated workbooks checked
out clean: CI 267.8 vs Forecast EW grand total 268, BR 275 vs 275 exact, JX 252.3 vs 252,
all within rounding, and Forecast 2-way agreed with Forecast EW on all three (PTEW holding
as a genuine rate, as it should). No "PDEW" anywhere on any of the three. John attached the
three corrected files to the waiting draft and sent it. Nothing further to do here.

### Task 1 - Deploy today's code to the workstation, correctly

The known trap, hit twice already this week per `HANDOVER-19Aug2026.md`: running
`Meridian-run.bat` over an already-live server just re-warms the OLD process. The window
must be closed - actually ended, not just left running in the background - before the bat
runs again.

**Workstation Remote** (pull)

```powershell
cd C:\src\meridian
git pull
git log --oneline -3
```

Expect the top commit to read `5edb8d3 Task 60: wire the basis label into route_deck.py...`
If it doesn't match, stop - do not restart the server on a partial pull.

**Workstation Actual** (restart - kill the window first)

```powershell
cd C:\src\meridian
.\Meridian-run.bat
```

Before running the block above: close the Meridian console window itself (not just
minimise it, not Ctrl+C into a prompt - end the process), then run the bat fresh.

**Pass/fail**: hard-refresh the dashboard, run a fresh SJC-TPE forecast, confirm the
acceptance figure (131,812 at 2026, 5x) still lands. If it doesn't reproduce, do not let
testers near the portal - diagnose first.

### Task 2 - Prove the "0 finds" fix live, and eyeball today's labelling fixes on a real pack

Two separate checks, both need the live server from Task 1.

**Workstation Remote** (the model-ID fix - this is the one with no sandbox equivalent)

```powershell
cd C:\src\meridian\app
py -3.12 test_research.py
```

Expect real findings back, not an empty list and not an exception. If it still returns
nothing, the model-ID fix in `research_provider.py` didn't resolve the underlying cause,
and this needs diagnosis before testers touch Stage 2 researched pitches - do not assume
the fix worked just because the code compiles.

**Then, from the dashboard**: run SJC-TPE (or any live route) with a researched pitch, and
download both the digital HTML pitch pack and the route deck (pptx). Confirm by eye:

- The HTML pack states base year, forecast year and each-way/two-way basis on the traffic
  forecast table, connecting markets, schedule and capacity table, and route economics
  panel - this was John's exact complaint yesterday, and it was only checked against
  synthetic fixtures in this session, never a real generated pack.
- The route deck's forecast slide states "each way (X both ways/yr)" on all four stat
  boxes (addressable market, captured point-to-point, connecting feed, total forecast),
  not just the two it used to.
- If `full_report` was requested, the five-year build table's "Carried (EW)" column and
  the connecting feed detail table's "PTEW (EW)" / "Annual (EW)" headers render without
  visual overflow - this was checked against LibreOffice's renderer in the sandbox, not
  PowerPoint itself, so a real open-in-PowerPoint check is worth the extra minute.

**Pass/fail**: both packs show clear, self-standing basis labelling with no reliance on
surrounding prose to understand what a number counts.

### Task 3 - Confirm or rotate the exposed Anthropic key

Earlier this week, a PowerShell paste error exposed a fragment of the real
`ANTHROPIC_API_KEY` in the terminal transcript (the "...DCVmiAAA" fragment). This was
flagged at the time with a recommendation to rotate it. **This needs a direct answer from
John**, not an assumption either way:

- If it was already rotated: confirm the new key is the one live in
  `anthropic_key.txt` on the workstation (beside `research_provider.py`, in `app/`), and
  that Task 2's `test_research.py` run above used it.
- If it was not rotated: generate a new key in the Anthropic console, replace
  `anthropic_key.txt` on the workstation, re-run Task 2's `test_research.py` check against
  the new key, and only then consider this closed. Do not leave a possibly-compromised key
  live for three days with testers using the product and nobody watching.

### Task 4 - One clean regression baseline, dated today

Nobody has run the full suite together since these fixes landed; each fix was verified in
isolation. A single dated "this was green" point matters more once testers start reporting
things, so there's something to compare against.

**Workstation Remote**

```powershell
cd C:\src\meridian\app
py -3.12 -m pytest test_workbook_table.py test_airport_profile.py test_alliance_share.py test_attribution.py test_check_airport.py test_competition_split.py test_contract_p2p_row.py test_demo_flow.py test_economics_wiring.py test_fare_bands.py test_feed_provenance.py test_floor_only_arm.py test_load_aci.py test_mct.py test_network.py test_qsi_feed.py test_qsi_score.py test_refresh_pickup.py test_regression_v2.py test_route_case.py test_route_forecast.py test_schedule_sizing.py test_track_control.py test_watch_series.py -v
cd C:\src\meridian
py -3.12 test_deck_contract_ptew.py
```

(`test_research.py` deliberately excluded from the pytest batch - it hits the live API and
costs money per run; it was already run standalone in Task 2.)

**Pass/fail**: paste the full output back. Any red result gets diagnosed before testers
start, not left as a known-flaky test - if a test is genuinely stale rather than a real
regression, say so explicitly rather than skipping silently, per the house rule against
silent fallbacks.

### Task 5 - Confirm testers can actually get through the door

Meridian sits behind two separate gates: a shared-password HTTP Basic Auth gate
(`QSI_PASSWORD`, env or `access_password.txt` beside `cortex_app.py`) in front of every
route, and a Cloudflare Access email-OTP policy in front of that. Both need to be right
before John leaves, or testers are locked out for three days with nobody able to fix it.

- **Ask John for the testers' email addresses**, and confirm each one is on the Cloudflare
  Access allowlist for aviacortex.com. This session cannot check or edit that policy - it's
  a Cloudflare dashboard action, not a code change.
- **Distribute `QSI_PASSWORD` through something other than pasted chat text or a terminal
  transcript**, given Task 3. A password manager entry or a direct message is fine; don't
  repeat this week's exposure pattern with a second secret.

### Task 6 - Triage the progress-indicator gap before it generates false bug reports

Runs over roughly 10 seconds show no progress indicator; Routes has been measured at up to
3 minutes over wifi (15 August). A tester who doesn't know this will report "it's broken"
or "it hung", not "it's slow" - and John won't be there to correct the record in real
time. Per `meridian-long-run-feedback` memory, the design for a loading/radar indicator
already exists (found at `/signin`, not lost, just never wired into the main run path).

This is a genuine judgement call for whoever picks this up, not a scripted step: either (a)
wire the existing design into the long-running paths before John leaves, if there's time
today, or (b) if there isn't, send testers an explicit one-line warning ("some runs take a
couple of minutes with no visible progress bar yet - that's expected, not a bug") before
they start. Don't leave this un-decided; a silent gap here is the single most likely
source of noise in John's inbox when he's back.

### Task 7 - Draft the testers' "known, don't report this" list

A short list, sent to testers alongside their login details, so John's first day back is
spent on genuine findings rather than re-triaging his own backlog. Draft from what's
actually parked, not a generic disclaimer:

- Frequency shows as a bare weekly count; there's no day-of-week allocation yet
  (`meridian-day-allocation-backlog` memory).
- The competition slide is deliberately absent from packs; it waits on Job 3
  (`meridian-pack-maps-16aug` memory).
- The floor A/B setting is under active review during the beta and may move
  (`qsi-floor-ab-16aug` memory).
- Whatever Task 6 lands on, state it explicitly here too.

Send this with the login details, not buried in a separate document testers won't read
first.

### Task 8 - Flag the Atlas wording decision to John directly

Separate repo, separate chat (the Atlas build chat), this session has no visibility into
its current state. The 16 August note
(`C:\AviaDev\NOTE-Atlas-QSI-current-method-16Aug2026.md`, section 4 item 4) is explicit
that the accuracy-claim wording decision needs John's sign-off "before you leave," with
both the current wording and the ruling's wording put in front of him, and a stated
deadline of 26 August - the same window as his departure. **This is not a task this
session can close.** The action is simply: ask John whether it's been actioned, and if not,
make sure it reaches him before he leaves. Do not attempt to make the wording call on his
behalf, and do not reach into a repo this session has no access to and guess at its state.

## 5. Machines, paths, conventions (standing, carried from 19 Aug)

- **Command block convention (non-negotiable)**: every block labelled DevPC / Workstation
  Remote / Workstation Actual, opens with the `cd`, one machine per block, commands only.
  John pastes transcripts back; read them fully, they are the ground truth.
- **DevPC clone**: `C:\AviaDev` (app/, deck/). Handovers, runbooks, briefs and
  `COMMIT-MSG-*.txt` files live here too. The Cowork mount of it denies delete/overwrite
  for git purposes, and this session confirmed `git status` itself throws a lock-cleanup
  warning (harmless, read still completes): **never run `git commit` or `git push` against
  the mount.** Write code with the file tools, give John the commit block, he runs it.
- **Workstation (donatello)**: clone `C:\src\meridian`, data on `E:\Avia` (sabre.duckdb
  286.5m rows, oag.duckdb 210.8m rows), contracts in `E:\Avia\contracts`, portal via
  `Meridian-run.bat`. Remote route: ssh as `aviaremote1` (Tailscale); RDP evicts whoever is
  at the screen. Z: (Egnyte) is per-logon and invisible in ssh sessions.
- **scp transfer point on DevPC**: `C:\Avia_extracts`. No wildcards to the Windows
  workstation - name every file. SHA256 both ends when it matters.
- **Cloudflare**: meridian/atlas live at aviacortex.com behind email policy + OTP;
  100-second rule is why `/api/report` and `/api/optimise` are background jobs;
  `/api/forecast` remains a watch item.

## 6. Traps that burnt us (carried, plus new ones from this week)

1. `Meridian-run.bat` over a live server re-warms the old process. Kill the window first.
   HTML now ships `Cache-Control: no-cache`, but the server process itself must be
   restarted, not just the page reloaded.
2. John pasting prose into PowerShell caused a junk commit and a force-push recovery once;
   this week it also caused a real API key fragment to land in a terminal transcript.
   Command blocks are commands only - this now matters for security, not just for git
   hygiene.
3. **A wrong-but-plausible-looking model ID string fails silently.**
   `"claude-sonnet-4-6"` looked like a real Anthropic model name and wasn't; the calling
   code's `except Exception: return [], {"error": ...}` pattern meant a bad model ID and a
   genuinely-empty research result were indistinguishable from the outside. If a
   research/API integration EVER reports "0 results" with no visible error, check the
   actual exception in `search_meta`/`audit["blocks"]` before assuming the query itself
   found nothing.
4. `git status` on the DevPC mount throws an `index.lock` unlink warning even as a
   read-only check (this session, 23 August). It didn't break anything, but treat it as
   confirmation, not just a rule someone wrote down once, that this mount is not where git
   writes happen.
5. scp to the Windows workstation: no wildcards, name each file.
6. Downloads must never silently fall back: `lastQ` is the run on screen, optimise seeds it
   from the result picks, refusal scrolls into view. If a download refuses, the cause is a
   stale page or a cleared run, not the engine.

## 7. Standing rulings in force

- **One Meridian model**: one engine, 60% by route, 86/92 grouped. Never a second engine,
  never lower the claims.
- **Naming**: product is Meridian, published by The Aviation Observatory. Client surfaces
  say "Meridian analysis, The Aviation Observatory." Avia Cortex is a dev name only, never
  client-facing. Filenames `Meridian_*`.
- **Sabre compliance**: attribution is the single constant in `app/attribution.py`
  ("Sabre Global Demand Data"); fares leave the server as bands only
  (`app/fare_bands.py`); single-route blind figures are never client-facing.
- **Download fidelity**: a download reproduces THE RUN ON SCREEN. `api_report` calls
  `api_forecast`; by construction they cannot differ.
- **NEW this week - the each-way/two-way convention**: US-domestic routes state passenger
  counts each way; every other route, including SJC-TPE, states two way. The classifier
  lives in exactly one place (`forecast_to_contract.case_and_outputs`); every display
  surface either reads `contract["_demand_basis"]` or, where it doesn't consume the
  contract directly (route_deck.py, pitch_html.py), states its OWN basis explicitly rather
  than assuming the reader knows. Capacity, schedule, revenue, yield and fares are never
  wrapped by this convention - they are operational/financial facts, not a passenger-count
  choice.
- **NEW this week - PTEW, not PDEW**, is the correct label wherever a rate is "passengers
  per trip each way" against the route's OWN scheduled departures, not a flat calendar-day
  or flat-728 assumption. Swept across `deck_contract.py`, `route_deck.py`,
  `forecast_to_contract.py`; if a new surface computes a similar rate, check it isn't
  reintroducing the flat-basis version of this bug.

## 8. Explicitly OUT of scope for this push

To stop the next chat from scope-creeping into the wider backlog under time pressure. None
of the following block "ready for testers":

- The post-Sabre queue from `HANDOVER-19Aug2026.md` section 10 (R6/R7 depth, R9 query log,
  R17 ToU, R18 demo mode, pitch-job one-run alignment, portal-as-service, catchment map
  restyle, fleet delivery layer, SJC curfew confirmation, appendix variants, Sabre/OAG
  confirmation letters).
- The SJC short-deck ask for Mark Kiehl (`sjc-short-deck-mark-ask` memory) - explicitly
  blocked on Mark's own finished master deck, unrelated to Meridian's general
  test-readiness.
- `genoa_nyc.py`'s `a.ppt` deck path, which calls `build_deck()` with a forecast dict shape
  that predates the current signature and would `KeyError` if run - a pre-existing break
  in a one-off case script, not a regression from anything this week, not fixed and not
  urgent.
- Any new feature work of any kind. This week is deploy, verify, and triage what's already
  built - not build more.

## 9. Key files, one line each

- `C:\AviaDev\HANDOVER-19Aug2026.md` - the previous handover (Sabre demo week).
- `C:\AviaDev\NOTE-Atlas-QSI-current-method-16Aug2026.md` - the Atlas note; section 4 item
  4 is task 8 above.
- `C:\AviaDev\COMMIT-MSG-22Aug2026-domestic-international-basis.txt`,
  `COMMIT-MSG-22Aug2026-deck-contract-basis-fixes.txt`,
  `COMMIT-MSG-22Aug2026-ew-2way-tab-pairs.txt`,
  `COMMIT-MSG-22Aug2026-research-model-and-pitch-html-labels.txt`,
  `COMMIT-MSG-22Aug2026-route-deck-basis-labels.txt` - full detail behind section 3's
  summary, one per commit.
- `C:\AviaDev\app\test_research.py` - the live-API smoke test for task 2; costs money per
  run, don't add it to routine pytest batches.
- `C:\AviaDev\app\test_deck_contract_ptew.py`, `C:\AviaDev\app\test_workbook_table.py` -
  this week's two new/extended regression suites, 27/27 and 22/22 respectively as of 22
  August.
- `C:\AviaDev\app\research_provider.py` - the "0 finds" fix; `DEFAULT_MODEL` and
  `_load_api_key()` are the two functions that matter.
- `C:\AviaDev\app\pitch_html.py`, `C:\AviaDev\app\route_deck.py` - today's two labelling
  fixes.
- `C:\AviaDev\app\cortex_app.py` and `C:\AviaDev\app\app_avia_style\cortex_app.py` - the
  known duplicate pair; both were touched today (`has_key`, `captured_2w`/`feed_2w`) and
  both need to stay in step. This duplication is itself a standing Avia Tool Standard gap,
  not fixed this week.

---

## 10. Pickup prompt for the new chat

Paste this as the first message:

> Continue the Meridian readiness push. Read, in order: (1) your memory index MEMORY.md
> and its READ-FIRST files, (2) C:\AviaDev\HANDOVER-23Aug2026.md, which is the state of
> play and is newer than memory where they differ. This handover's section 4 is a punch
> list of eight tasks to complete today, in order, so Meridian (and separately, Atlas) are
> ready for a team of testers while I'm on holiday from about 26 August. Work through them
> in order; task 1 (workstation deploy) and task 4 (regression baseline) need me to paste
> command-block transcripts back before you can confirm pass/fail, so ask for those as you
> reach them rather than assuming. Tasks 3, 5 and 8 need a direct answer from me (key
> rotation status, testers' email addresses, Atlas wording sign-off) - ask, don't guess.
> Command blocks stay labelled DevPC / Workstation Remote / Workstation Actual with the cd
> first and commands only; never run git commit or push against the mounted repo.

---
*Avia Solutions internal. 23 August 2026. Session handover, complements
HANDOVER-19Aug2026.md and the memory store.*
