# Handover: one Meridian model, a scenario runner, and the basis problem underneath both

Version 1.0, 12 August 2026 evening. Avia Solutions. Written for a fresh Cowork session.

Supersedes *HANDOVER Meridian - one model and a scenario runner - 12Aug2026.md*. That document's
Task 1 is delivered, its Task 5 is proved, and its Task 4 is still held, but for a reason it did not
know about. Read *commit-message-12Aug2026.txt* for the wiring fault found in the morning and
*GRADING-BASIS-QUESTION-12Aug2026.md* v3.0 for the question that now decides everything.

Paste the fenced block into a new chat. Everything after it is the detail.

---

```
FIRST, THE MOUNT, BEFORE YOU READ ANYTHING ELSE.

Cowork attaches the PROJECT folder automatically, which is
C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool. THAT IS NOT THE REPO. It holds the
handovers and kickoffs and it also holds a STALE app\ copy dated 7 August, cortex_app.py at 1,627
lines against the real 2,154, which predates the connecting build and looks exactly like a working
copy. Do not read it and never write to it.

THE REPO IS C:\AviaDev. Not C:\AviaDev\meridian: .git, app\ and bt2\ sit directly in it. ASK FOR IT
YOURSELF with the folder-access tool rather than waiting to be offered it, and ask for E:\Avia and
C:\Avia in the same breath. You have it when app/econ_baseline.py and bt2/bt2_experiments.log are
both inside the mount and app/cortex_app.py is 2,154 lines. C:\src\meridian is the WORKSTATION copy
and will usually not attach; that is fine, John runs there.

THE TWO MACHINES, and do not get this wrong:
  Dev PC       C:\AviaDev        Cowork attaches HERE. Everything you write lands here and nowhere
                                 else. Edit here. John commits and pushes from here.
  Workstation  C:\src\meridian   plus the data root E:\Avia. John pulls and runs everything there.
Code moves ONLY by git push on the Dev PC then git pull on the Workstation. Never tell John to run
something you have just written without that step first. LABEL EVERY COMMAND BLOCK WITH THE MACHINE,
including blocks with nothing to run.

NEVER RUN GIT, not even a read-only `git status`. It strands .git/index.lock on the mount and blocks
John's commits. Answer provenance questions with ls, md5sum and reading files. Hand John commit
messages as files and he runs every git command himself. ANOTHER SESSION MAY BE IN THIS REPO: tell
him to run `git status --short` and read it BEFORE composing any `git add`, and name only the files
you wrote.

POWERSHELL: $env:NAME = "value", never `set`. ONE-LINE commands, no backtick continuations. A fresh
shell loses everything. Every Workstation session sets AVIA_LOCAL_CACHE, AVIA_OAG, AVIA_SABRE and
AVIA_FREQ_SENSITIVE = "1", plus AVIA_BT2_DIR = "E:\Avia\bt2_relaxed" for anything touching BT2.
John runs as aviaremote1 over SSH, a DIFFERENT Windows user from Carte with its own site-packages;
scikit-learn was installed there on 12 August and that install moved a published figure, see below.

THE STATE OF IT IN THREE SENTENCES. There is still ONE ENGINE ANSWERING CLIENTS and it is the QSI
engine: cortex_app.py, route_forecast.py and route_feed.py contain no reference to bt2_forecast,
route_context or AVIA_FORECAST_ENGINE, so the switch remains inert and the calibrated model is not
wired. What changed on 12 August is that wiring it is now POSSIBLE without silently feeding it a
wrong feature, and that a tester can run scenarios without writing Python. What was found is that
the published accuracy describes a test three steps removed from what the app does, and no
arrangement of the wiring changes that.

THE MEASUREMENT THAT DECIDES THE SESSION. Blind against blind, on the same 1,555 routes, the
calibrated model scores 55.4% within +-20% on its own population, target and grading year, and
22.4% on the pin's. Population, target and year cost 33 points between them. The model still beats
the Cortex path on both denominators, 22.4% against 12.6% on the local market and 28.9% against
14.5% on the whole sector, both p<0.0001, so the one-model direction is right and there is no case
for stopping. But the published 92% and 86% are a FITTED figure on top of all this, and what they
describe is not what a client is served.

THE PUBLISHED CLAIMS STAY unless John decides otherwise. Do not propose trimming them. Do not
propose a fallback between engines: a case the calibrated layer handles badly is handled inside the
one model by giving it the right input.

WORKING RULES. Verify, do not assert. On 12 August SEVEN conclusions were withdrawn between John and
two Cowork sessions and the pattern was identical every time: reaching for a measurement without
first establishing that the two quantities were comparable. BEFORE comparing two numbers, state what
basis each is on. Check every number against one John already knows and tell him BEFORE anything
else if a change moves it. Tell him when he is wrong and show him the measurement; he was wrong once
on 12 August and said so, and so was the session, twice, in the opposite direction on the same
question. Ask before running anything over about twenty minutes. House style throughout, including
code comments.

READ FIRST: bt2/bt2_experiments.log, the 12 August entries, most recent first. There are 282 lines
and the last eighteen are from the evening of 12 August.
```

---

## 1. The three questions John asked, answered from the code rather than from memory

### Is there a single Meridian model now?

**No, and it is worth being exact about what is and is not true.**

`cortex_app.py`, `route_forecast.py` and `route_feed.py` contain no reference to `bt2_forecast`,
`route_context`, `bt2_capture_core` or `AVIA_FORECAST_ENGINE`. Checked by grep on the live tree on
12 August. So the switch is still inert because nothing in the running path imports the module that
reads it, exactly as the morning's handover said. `cortex_app.calibrated_forecast` at line 687 is
the QSI engine and is the single place a client number is produced.

What changed is the state of the thing that would be wired in.

| | morning of 12 August | evening of 12 August |
|---|---|---|
| `route_context` builds capa | from the engine's `qsi_share`, a different quantity | from `bt2_capture_core`, the training implementation |
| `route_context` builds qcx | one direction, from engine sums | both directions, training definition |
| `route_context` builds legs_n | the connection-set count from `route_qsi` | `len(legs)` from the training leg query |
| agreement with training | never measured | 246 of 250 routes identical |
| the wiring | would have fed feature 3 a value below the tenth percentile of training on every route, silently | would feed it the quantity it was trained on |

So the answer is: one engine answers clients, it is the QSI engine, and the calibrated model is now
ready to be wired for the first time. Task 4 is held on the grading basis, not on the wiring.

### If John runs it, does it include everything from the past week?

**Yes for the QSI engine, and the proof is that two independent reproductions came back exact.**

`econ_baseline.py capture` on commit `bd4ffe6` returned all twelve figures identical to the 12
August SJC-TPE-BASELINE entry: BR B77W 4x 121,212 two-way with P2P 54,486 and connecting 66,726, CI
A359 5x 139,230 with 62,586 and 76,644, CI B789 7x 203,840 with 91,630 and 112,210. And the
scenario runner reproduced the frequency ladder to the passenger: 2027 4x 109,764 on 127,296 seats
at 86.2%, 2027 5x 119,306 at 75.0%, 2028 4x 117,448 at 92.3%, 5x 127,658 at 80.2%, 6x 137,200 at
71.9%.

So the running path carries the 11 August connecting build in full: the hub local-time fix, the
alliance code fix, the OAG board dedupe, the symmetric hub exclusion, the one counting rule, the
departure optimiser, curfews, named partner carriers, the forecast year and the growth path, and
the split floor.

**Three qualifications, and the second is serious.**

`AVIA_FREQ_SENSITIVE` still defaults OFF in `route_forecast.py` line 561. `warm_demo.py` now sets it
in the server environment, so the portal is right, but any command-line run without it returns the
same demand at 3x and at 14x and only the load factor moves. The scenario runner refuses to run
without it for that reason.

**The live path runs the QSI connecting feed that the back-test says does not ship.**
`cortex_app.py` line 850 sets `qsi_feed: True` whenever a departure time exists, which is whenever
an airline is named. QSI-FEED-CLEAN of 12 August measured that feed as measurably worse: 15.1% to
12.7% within +-20% on 2,963 paired routes, +43 -112, p<0.001. Every SJC-TPE figure quoted this week
was produced with it on. That is a direct conflict between what was measured and what ships, and it
was not noticed while the measurement was being made. It may be defensible, because the back-test
configured the feed differently from the live path, but nobody has established that. **It is the
first thing to settle after the grading basis.**

The calibrated model is not in any of it. And on the Dev PC the water-boundary mask is not
installed, so island and coastal catchments over-read there; `warm_demo.py` prints the state and the
install line.

### What is left to do

In the order it should be taken. Detail on each in section 6.

1. **The grading basis.** Blocks Task 4 and nothing else can be quoted until it is settled.
2. **The QSI feed conflict above.** Shipped behaviour contradicts a measured result.
3. **What "re-anchored" means in `bt2_pin_score`.** The evening's headline figures cannot be quoted
   beside the 60.4% until it is defined.
4. **Task 4, the wiring**, once 1 is settled.
5. **Task 3, the leaked secondary airport**, now sized: 1,517 routes the calibrated model cannot
   answer at all.
6. **The 2015-2017 OAG region gap.** Needs a load from Egnyte before any rebuild.
7. **The 2018-08 label staleness.** 37 rows in one cohort.
8. **NNG-YTY.** One route, unexplained.
9. Everything already carried in the morning handover: the optimiser objective, the 87.5% plan cap,
   the `M` counter, the `if feed_cfg` shape, the open portal.

## 2. What was built on the evening of 12 August

Five files new, three changed. All on the Dev PC, all pushed by John.

| file | what it is |
|---|---|
| `app/scenario_runner.py` | NEW. A file of cases in, a table out, no Python written by the tester |
| `app/cases_sjc_tpe.json` | NEW. Sixteen worked cases to edit |
| `app/bt2_capture_core.py` | NEW. The one implementation of the three disputed inputs |
| `app/bt2_input_check.py` | NEW. Does the live path reproduce training on the training routes |
| `app/oag_label_check.py` | NEW. Which OAG labels are complete, and what a region count does not tell you |
| `app/route_context.py` | CHANGED. capa, qcx and legs_n no longer read from the engine payload |
| `bt2/bt2_capture.py` | CHANGED. Imports the shared implementation rather than holding its own |
| `bt2/bt2_experiments.log` | 18 new entries |

### The scenario runner, which was Task 1

`app/scenario_runner.py` generalises `app/econ_baseline.py`. Cases may be JSON with a `defaults`
block or a CSV with one case per row, and carry route, carrier, aircraft, seats, frequency, forecast
year, growth path, departure time, partner carriers, split floor, plan cap, season and curfews.
Every figure comes from `cortex_app.calibrated_forecast`, so a scenario run and the portal answer
the same question with the same code; if the two ever disagree that is a defect in the runner.

Everything is reported TWO-WAY and every doubled column says so in its name. `demand_lf` and
`plan_lf_achieved` are separate columns: the first is total demand over seats and answers whether
the demand is there to fill the aeroplane, the second is carried over seats, is capped, and can only
ever be the lower. Reading one for the other is the capped-against-uncapped error that invalidated a
comparison quoted for a week.

It fails loudly on a payload key it does not recognise, refuses to write a table in which any case
errored, refuses to run without `AVIA_FREQ_SENSITIVE`, and rejects a misspelled setting by name
rather than ignoring it.

Sixteen cases ran green on the Workstation. Starlux returned numbers and a traffic-rights verdict
rather than the blank it was silently reduced to on 9 August.

### The three inputs on one implementation

`load_legs`, `components` and `cap_from` moved out of `bt2/bt2_capture.py` into
`app/bt2_capture_core.py`, and both chains import them. That is John's ruling of 9 August applied to
the three inputs it had not been applied to.

Two things worth knowing before touching that file. **A single-week OAG label is refused by name.**
Training read a MONTH and took the schedule rows covering the 15th to the 21st; handing `load_legs`
a label like `2026-05-25` builds the date window `2026-05-25-15`, which is not a date, returns no
legs, and a route with no legs reads as a route with no competition and scores a capa of 1.0. And
**two quantities are called qcx and they are not the same**: inside `cap_from` it carries the 0.20
one-stop factor and covers one direction, while the model FEATURE sums both directions and carries
no such factor. Each is built by its own named function and neither is derived from the other.

## 3. What was measured, with the numbers

### The live assembly against training, `bt2_input_check`, cohort 2018

| sample | capa | qcx | legs_n | median ratio |
|---|---|---|---|---|
| n=250 | 246 of 250 | 246 of 250 | 245 of 250 | 1.0000, p25 0.9999, p75 1.0001 |

This is the test `bt2_wiring_test.py` could not be. That one proved `bt2_forecast._vec` and
`bt2_g12_exp.X_of` build the same vector FROM THE SAME INPUTS, feeding both sides from the training
rows, and never called `route_context` at all.

### Task 2, the pin score, one sample and both numbers

n=1,555 routes scored by both, being the 50.6% of the arm's 3,072 the calibrated model can answer.

| graded against | Cortex path | calibrated model | McNemar |
|---|---|---|---|
| pure P2P outturn, the local market | 12.6% | 22.4% | +308 -157, p<0.0001 |
| total outturn, the whole sector | 14.5% | 28.9% | +371 -148, p<0.0001 |

Native blind on the four pin cohorts 60.2%, n=4,287, Sabre throughout. **And the number that
matters: 55.4% on the model's own population, target and year against 22.4% on the pin's, blind
against blind, same 1,555 routes.**

### The connectivity floor, measured on the shipped path for the first time

FLOOR-INVISIBLE records that the back-test cannot see the floor at all, because `route_forecast`
line 760 computes carried BEFORE the floor block and the floor only re-splits that total. The
scenario runner reports the post-split figures, so it can. SJC-TPE, China Airlines A350-900 at 306
seats, 4x weekly, 2028, identical in every other setting, two-way:

| | P2P carried | connecting carried | total | spill |
|---|---|---|---|---|
| floor OFF | 83,408 | 27,976 | 111,384 | 6,064 |
| floor ON | 50,068 | 61,316 | 111,384 | 6,064 |

Total-preserving exactly as line 767 states. **The floor moves 33,340 two-way passengers off the
local leg**, taking the connecting share from 25.1% to 55.0%. Open item 2 answered by observation.

### Two properties of the engine that will be asked about in a room

**P2P is carrier-blind.** At a given frequency on a given route every carrier returns the same local
number and they differ only on the feed. SJC-TPE 2028 at 7x: EVA, Starlux and United all carry
112,132 P2P two-way and differ on connecting at 39,792, 22,262 and 37,234. That is the design, since
P2P comes from the measured airport capture factor and the frequency shape while the feed comes from
the carrier's own network. It is correct and two airlines in the same room get the same local
number, so have the answer ready.

**The capture share is the same for every carrier at a frequency.** 25.10% at 4x, 27.56% at 5x,
29.85% at 6x, 32.00% at 7x on SJC-TPE, where 32.00% is the measured airport factor and 7x is the
reference frequency. Same reason.

### The MCT master, and what it says about the training data

**The training capture was built with no minimum connect time master at all.** Measured on cohort
2018: with the master loaded, 20 of 40 routes stop matching what `bt2_capture` already wrote and
every one reads high, median ratio 1.0549, upper quartile 1.3637, maximum 1.8379. Without it, 39 of
40 agree to the file's own write precision. So `capa`, the third feature of the model behind the
published 92% and 86%, was computed with the 90 minute default at every airport, and that was not
written down anywhere.

Both chains now default OFF so the live path reproduces training. `AVIA_BT2_MCT=1` turns it on and
means rebuilding the cohorts and re-measuring the model. The master itself is not in question: E:
and C: hold byte-identical copies, md5 `2d7e8a27f2f167b4992345b1f4fde299`.

### The OAG store, 2015 to 2017

`oag_label_check --coverage` on distinct departing flights in August, which carry no region
duplication:

| | 2015 | 2016 | 2017 | 2018 | 2019 |
|---|---|---|---|---|---|
| JNB | 21 | 26 | 24 | 401 | 402 |
| CAI | 48 | 49 | 50 | 382 | 337 |
| DXB | 356 | 375 | 381 | 639 | 626 |
| DOH | 175 | 197 | 220 | 348 | 366 |
| TPE | 372 | 423 | 406 | 421 | 451 |

**Asia is complete throughout, so the Asian ingest is sound.** What is short is intra-Africa and
intra-Middle-East flying. What survives in 2015-2017 is the flying that had somewhere to live in one
of the five loaded partitions: Dubai keeps 60% because its long-haul into Europe and Asia sits in
those files, Johannesburg keeps 6% because nearly all its flying is intra-African.

Cohorts 2016 and 2017 take every pre-launch month from that range, so their `capa`, `qcx` and
`legs_n` were measured against a world missing most African and intra-Gulf connectivity, and the
model is fitted on them. **`bt2_input_check` cannot see this**: both chains read the same store,
agree perfectly, and agree on a number built from a partial schedule. It reaches past BT2, since the
QSI engine reads the same store and the 4,342-route pin has 2016 and 2017 among its four cohorts.

Unproven and worth testing: the BY-COHORT entry of 9 August has 2016 at 51.1% and 2017 at 53.4%, the
two lowest of six, against 2018 at 57.7%, 2024 at 58.5% and 2025 at 58.1%. 2019 sits at 53.3% on
complete labels, so the correlation is not clean.

## 4. Conclusions withdrawn on 12 August, so they are not re-proposed

Seven, and the pattern is identical in all of them.

| withdrawn | what it was | what settled it |
|---|---|---|
| capped against uncapped, twice | the 1.03x agreement with the 2025 analyst compared our capped carried against his uncapped demand | John held it against a number he knew |
| the analyst's connecting figure as a target | it inherits the same Sabre under-count our raw feed does | FLOOR-EVIDENCED, outturn on 335 and 476 routes |
| the load-factor cap from the back-test | capacity annualised at 52 weeks against actual outturn | the figures were not load factors |
| the input-check tolerance | compared at 1e-9 and 1e-6 against a file written at 3 and 5 decimal places, reporting 32 of 40 false failures | the median ratio was 1.0000 |
| the MCT master explaining NNG-YTY | it returns 0.3822 with the master and without it, to four decimals | running it both ways |
| the failures being an Asia problem | TW, JP, KR, SG, TH, VN, MY, ID, PH, MO, MM, BN all pass | the country breakdown |
| all regions present under an EMEA taxonomy, John's reading | EMEA-as-Europe would have kept Johannesburg whole | 24 distinct departures at JNB in 2017-08 against 402 in 2019-08 |

The last two are worth keeping together: the session and John were wrong in opposite directions on
the same question, and one query settled both. A region count counts DOWNLOAD PARTITIONS. Coverage
is distinct flights at named airports, because rows carry the region duplication and distinct
flights do not.

## 5. Two things that must be closed before any figure is quoted

**What does "re-anchored" mean in `bt2_pin_score.py`?** A model that forecasts the LOCAL market
scores BETTER against the larger sector denominator, 28.9% against 22.4%, which is the wrong way
round for a local forecaster held against a denominator that adds connecting passengers. Either the
re-anchoring changes the quantity being predicted, or the model over-reads local traffic on this
population and the sector denominator is simply nearer. The session that wrote the script knows.
None of the evening's figures sits beside the 60.4% until it is answered.

**A published blind figure moved with a library version.** The same script on the same artefacts
returned 59.8% on the Dev PC on 12 August and 60.2% on the Workstation that evening, identical
n=4,287 and identical configuration. aviaremote1 is a different Windows user with its own
site-packages and had scikit-learn installed fresh that night. `HistGradientBoostingRegressor` was
recorded as deterministic on 9 August, ENS-6C, so the seed is not it. Pin the version or record it
in `bt2_claimset` beside the figure.

## 6. Open, in the order to take them

1. **The grading basis.** `GRADING-BASIS-QUESTION-12Aug2026.md` v3.0, with John. Questions 1 and 2
   are still open and are now the whole of it: is the engine's `p2p_carried` the same quantity as
   `launch_pax`, and what is `launch_pax` exactly. Question 3 is answered and question 4 has the
   floor measurement in it.
2. **The QSI feed conflict.** `cortex_app` line 850 turns on a feed the back-test measured as
   measurably worse. Establish whether the two configurations are the same thing before changing
   anything, because that is precisely the error this programme keeps making.
3. **"Re-anchored", and the version sensitivity.** Section 5.
4. **Task 4, the wiring.** `cortex_app.calibrated_forecast` line 687. Everything upstream stays;
   everything downstream reads the one number. Do not start it before item 1.
5. **Task 3, the leaked secondary airport, now sized.** 1,517 of the arm's 3,072 routes the
   calibrated model cannot answer. Three causes are mixed in that number: the pair was not virgin by
   the calibrated rule, or its market sat below the 250 training floor, which is the leaked
   secondary airport, or no capture row exists. Separating them needs a discovery pass and it is the
   first thing to do, because widening the discovery rule may be most of the remedy: the model does
   NOT weaken in thin markets, scoring 66.9% under 500 passengers against 53.1% above 20,000.
6. **The 2015-2017 region gap.** Load the Africa and Middle East workbooks from Egnyte for those
   years, then decide whether the capture is rebuilt and the model re-measured. Rebuilding against
   the store as it stands would change nothing. Size it first: how many of the 6,524 training routes
   have a connecting itinerary that would have run through an African or Gulf hub. A Norwegian
   domestic launch is unaffected; a long-haul launch competing against Emirates over Dubai is not.
7. **The 2018-08 label.** 37 rows in cohort 2018, written 9 August against a label the Asia fold
   changed on 11 August. Small, and it means the artefact is fitted on values the store no longer
   returns.
8. **NNG-YTY 2018-10.** One route in 250. Live reads 0.3822 of training on qcx and 1.0761 on capa,
   with `legs_n` identical, the minimum elapsed time identical at 104 minutes in both directions,
   and the same value with the master and without it. Same candidates, same best connection, fewer
   surviving. Not the label vintage, since it is 1 of 29 in its own month.
9. **Carried over from the morning handover, unchanged.** The departure optimiser scores connecting
   passengers only and should be tested with a connecting passenger weighted at 0.7 of a local one.
   The 87.5% plan cap is one global number for every carrier type and haul and can only ever
   under-forecast. The `M` counter cannot fire under `--jobs`. Three behaviours in `route_feed` key
   off `if feed_cfg` rather than off the named flag. The portal announces no password and demo
   sign-in on.

## 7. The run pack

### DEV PC

Editing only. `git status --short` before any `git add`, and name only the files you wrote.

### WORKSTATION, the environment, every session

```
$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_OAG = "E:\Avia\oag.duckdb"
$env:AVIA_SABRE = "E:\Avia\sabre.duckdb"
$env:AVIA_FREQ_SENSITIVE = "1"
$env:AVIA_BT2_DIR = "E:\Avia\bt2_relaxed"
```

### WORKSTATION, the four runs that matter

```
cd C:\src\meridian\app
py -3.12 bt2_input_check.py --cohort 2018 --n 250 --show 2
py -3.12 scenario_runner.py cases_sjc_tpe.json
py -3.12 econ_baseline.py check
py -3.12 oag_label_check.py --audit
```

```
cd C:\src\meridian\bt2
py -3.12 bt2_pin_score.py --arm C:\src\meridian\app\backtest_control_11Aug2026.csv --pin E:\Avia\backtest_routes_11Aug2026.json --out E:\Avia\pin_score_12Aug2026.csv
```

`econ_baseline.py check` should now report the commit changed and no figure moved. If any figure
moves, read the provenance block printed above the differences before calling it a regression: a
store refresh or an airportsdata release is a legitimate reason and a different thing.

## 8. The numbers a new session should hold everything against

SJC-TPE, China Airlines A350-900 at 306 seats, the 2025 analyst's 12:00 schedule, Southwest counted
as a partner, connectivity floor off so the connecting leg is comparable with his, post-recovery
growth at 7% a year, two-way demand against two-way seats.

| year | freq | demand | seats | load factor | P2P | connecting |
|---|---|---|---|---|---|---|
| 2027 | 4x | 109,764 | 127,296 | 86.2% | 82,196 | 27,570 |
| 2027 | 5x | 119,306 | 159,120 | 75.0% | 90,258 | 29,048 |
| 2028 | 4x | 117,448 | 127,296 | 92.3% | 83,408 | 27,976 |
| 2028 | 5x | 127,658 | 159,120 | 80.2% | 96,576 | 31,082 |
| 2028 | 6x | 137,200 | 190,944 | 71.9% | 104,606 | 32,596 |

The 2025 analyst: 107,857 two-way at 4x on 300 seats, YE2028, 86.4%, of which P2P 81,858 and
connecting 25,999.

And the three frozen baseline cases on commit `bd4ffe6`, two-way: BR B77W 4x carries 121,212 with
P2P 54,486 and connecting 66,726; CI A359 5x carries 139,230 with 62,586 and 76,644; CI B789 7x
carries 203,840 with 91,630 and 112,210. All three are CAPACITY BOUND at the 87.5% plan cap, so the
totals are seats times 0.875 and the demand model is not what sets them. Say "the aircraft fills"
rather than presenting them as a demand forecast, and quote the demand and spill beside them.

**Never compare against the analyst using `total`.** That is the capped carried figure and it agrees
with his 86.4% only because our 87.5% cap is near it. Use `total_demand` and `captured`.

Avia Solutions Limited. All rights reserved.
