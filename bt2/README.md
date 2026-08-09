# bt2: the accuracy programme

Version 1.0 - 8 August 2026 - Avia Solutions

The route-level back-test programme that produced Meridian's published accuracy claims. Brought into
the repo on 8 August 2026. Until then it lived only in `C:\Avia\bt2` on the Dev PC, unversioned, which
made the claims on the website and in every client deck the output of code that was not in git.

## Why it is inside meridian rather than its own repo

`bt2_capture.py` imports `connection_builder` and `schedule_chain` from `app/`, because BT2 is not a
standalone model: one of its fifteen features is the QSI capture share, and that is produced by
running the Meridian engine. Its output also feeds the engine's own track record page. A separate repo
would put a hard dependency across a repo boundary, which is what produced `AVIA_DECK_V4` and a
renderer nobody could find. One consumer means fold it in.

## What it is, in one line

From `bt2_model.py`: **capacity anchor.** `forecast_pax = seats_planned x exp(GBM median log O&D-per-seat)`.

The gradient-boosted median regression predicts O&D per seat from fifteen launch-conditioned features:
seats, base market, QSI capture, frequency, schedule density at the endpoints, haul, gauge, carrier
type, carrier identity for carriers with 15 or more launches, domestic flag, launch month, months
operated, connection-competition strength and capacity aggressiveness.

**What it does not produce.** A catchment, a leakage split by competing airport, a point-to-point
against connecting split, a hub connectivity picture, or any response to departure time. It produces
one number. That is why it cannot replace the engine, and why the open architectural question is which
layer owns the level rather than which engine wins. See the estate index.

## Provenance of the published claims

The claims are "calibrated 82% within +-10% and 89% within +-20% (2,915 launches, 2016-2019 and 2025)"
and "blind twenty-route portfolios 94% within +-20%", per John's binding ruling of 5 August 2026 in
`HANDOVER_Deck_Generator.md`.

Recorded here because the artifacts that produced them are **not** in this repo: they are build outputs
and computed intermediates, 42MB of them, and they live with the data. A claim that cannot be traced to
the artifact that produced it cannot be defended, so the hashes are the link.

| Artifact | Bytes | SHA-256 (first 16) | Written |
|---|---|---|---|
| `bt2_model.pkl` | 5,848,053 | `7426031c9661d5bf` | 29 Jul 2026 11:08 |
| `bt2_model_v1_1.pkl` | 6,460,032 | `565ed8338c03557f` | 05 Aug 2026 14:54 |
| `bt2_model_v1_2.pkl` | 6,481,957 | `27b665dcfce91b3a` | 05 Aug 2026 17:29 |
| `bt2_blind_preds.csv` | 197,691 | `e2d110e1f1c473ca` | 29 Jul 2026 10:19 |
| `fitted_dist.json` | 66,317 | see the store | 05 Aug 2026 17:20 |

`bt2_model_v1_1.pkl` is the production artifact, retrained on all five cohorts (n=2,915), and it
supersedes `bt2_model.pkl`. Note the distinction that matters in diligence: the **published** 88.8% and
82.4% come from the **light-regularisation** config on the mixed basis, while the production artifact
at production regularisation is fitted 72.1%. Both are recorded in `bt2_experiments.log` and the site
copy is explicit that the fitted figure tests whether the method is sound. Have the answer ready.

`bt2_experiments.log` **is** in the repo: 59 lines, one per experiment, and it is the record of what
was tried and what was rejected. It is the most valuable file here and the smallest.

## Paths

All resolution goes through `bt2_paths.py`. Nothing is hardcoded.

Until 8 August every script pinned its paths to a Cowork session mount,
`/sessions/wizardly-peaceful-tesla/mnt/...`, correct in the chat that wrote them and resolving on
neither machine. Twelve files, twenty-one occurrences, eight distinct targets. The practical effect was
that BT2 could not be run at all.

```
AVIA_BT2_DIR       where BT2 reads and writes its data and artifacts
                   Dev PC C:\Avia\bt2   workstation E:\Avia\bt2
                   SET THIS. Without it BT2 writes artifacts into the repo folder.
AVIA_LOCAL_CACHE   the data root, from which the stores are found
AVIA_APP_DIR       the Meridian engine folder; otherwise found by looking for cortex_app.py
```

```powershell
py -3.12 bt2_paths.py        # prints every resolved path, or NOT FOUND
```

## State of the migration, 8 August 2026

`bt2_capture.py` and `bt2_paths.py` are done. **Eleven files still carry the stale session paths** and
each needs the same substitution, deleting the hardcoded constant and importing from `bt2_paths`:

`_cpn_worker.py`, `_db1b_worker.py`, `bt2_base.py`, `bt2_coupon.py`, `bt2_db1b.py`,
`bt2_discover.py`, `bt2_growth.py`, `bt2_lib.py`, `bt2_metro.py`, `bt2_months.py`, `bt2_profile.py`

Nineteen occurrences. Mechanical, now the resolver exists. Do it before the next run, and prove it with
`bt2_paths.py` on both machines.

## The open question this programme has to answer

Meridian's live engine scored **16.9% within +-20% blind** on the control run of 8 August (296 of 1,747
forecastable routes), which reproduces BT2's own independent re-scoring of the method it replaced at
16.7%. BT2 scores 51% blind on its own harness. The learning in this programme therefore does not reach
the number Meridian returns: BT2 borrows the engine's capture feature and then discards the engine's
forecast.

The intended architecture, per John on 8 August, is one engine with the learned weights applied as a
correction at route level. The induced floor and the market-size-keyed P2P trim in `route_forecast.py`
already are that, fitted on a narrower feature set. The control run gives the refit a defined target:

| Base market | median forecast / outturn | n |
|---|---|---|
| under 15k | 1.77 | 781 |
| 15-50k | 1.18 | 753 |
| 50-150k | 0.89 | 198 |
| over 150k | 0.74 | 15 |

One coherent error with a clear shape, in a category that already exists. That is tomorrow's work, and
it is a refit rather than a search.

---

Avia Solutions Limited. All rights reserved.

## Running BT2 from PowerShell

Both the Dev PC and the workstation are PowerShell, where `set` is an alias for `Set-Variable` and
makes a PowerShell variable rather than an environment variable. A run started that way looks
configured and is not: on 9 August 2026 it resolved BT2 to the repo folder and stopped on a missing
`capture_2016.csv`, which is the guard in `bt2_paths` working, but the cause took a round trip to
find. Use `$env:`.

```powershell
cd C:\AviaDev\bt2
$env:AVIA_LOCAL_CACHE = "C:\Avia"          # E:\Avia on DONATELLO
$env:AVIA_BT2_DIR     = "C:\Avia\bt2"      # artifacts live with the data, never in the repo
$env:AVIA_APP_DIR     = "C:\AviaDev\app"   # BT2 imports the Meridian connection builder
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
$env:AVIA_BT2_BUDGET  = "130"              # bt2_capture seconds per invocation; 33 is the old cap
py -3.12 bt2_paths.py                      # prints all six resolved paths before anything runs
```
