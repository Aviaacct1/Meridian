# attic

Working scratch that is kept as a record and is not part of the tool.

Nothing here is imported by the service, nothing here is maintained, and nothing here should be
read as current. It is committed rather than deleted because a committed attic is a record and a
deletion is a loss: several of these scripts produced numbers that are quoted in
`BT2_BACKTEST_PROGRAMME.md` and in the accuracy notes, and the run that produced a figure is worth
keeping even when the script is finished with.

## The rule

A file arrives here with a one-line reason, in the table below, on the day it is moved. A file with
no reason recorded does not belong in the attic; it belongs in a decision.

Moving a file here is reversible and legible: `git mv` keeps the history, so `git log --follow` on
any file here still reads back to the day it was written.

## What is here, and why

### Moved 8 August 2026: the July accuracy search harness

The search over candidate accuracy adjustments, run through one scorecard, over roughly three weeks
in July 2026. It did its job: the results are written up in `BT2_BACKTEST_PROGRAMME.md` and in
`qsi-accuracy-plan`, and the adjustments that survived are in the engine. The scripts are numbered
iterations of the same idea rather than a maintained tool, and each carries a hardcoded input path
and a `/tmp` state file.

| File | Reason |
|---|---|
| `bench3.py`, `bench4.py` | resumable benchmark runners, state in `/tmp/qsi3c_state.pkl` and `/tmp/qsi4c_state.pkl` |
| `runner2.py`, `runner3.py`, `runner3b.py`, `runner4.py`, `runner4b.py` | successive back-test runners over the master tables; superseded by `backtest.py` flags |
| `score2.py`, `score3.py`, `score4.py`, `score_results.py` | scored the runs above and printed the within-band figures |
| `importance2.py`, `importance3.py` | feature importance over the master table, the work that fed the BT2 feature set |
| `subgroups.py`, `subgroups2.py` | cut the error distribution by segment, the work behind the airport-diagnosis method |
| `stage_runner.py` | staged the long runs so a single bash call could finish |
| `explore_segments.py` | one-off look at the T-100 segment table |

The master tables these read (`master_complete*.csv`, `master_v?_complete*.csv`, circa 11MB) are
gitignored as regenerable outputs, so a script here will not run without rebuilding them first.

## Still to decide, and not yet moved

The capability audit lists 59 modules that nothing imports and that have no command-line entry.
Seventeen of them are in the table above. The rest have not been reasoned about one at a time and so
have not been moved. They fall into groups worth taking together:

- **superseded versions of live modules**: `qsi_portal_v4`, `v8`, `v9`, `v10`, `v11`,
  `avia_dashboard`, `providers__1_`, `providers_v2_fixed`, `route_config_v2`, `route_config_v3`
- **the previous pipeline**: `avia_qsi_auto`, `avia_qsi_auto_v3` and its dependents. **Not attic
  candidates yet.** `avia_qsi_auto_v3` is the only route to `departure_time_grid.py`, which holds
  the specification and the reference numbers for the departure-time work: 129,162 passengers at a
  21:30 SJC departure against circa 139,302 at 17:00. Decide after that work lands, not before
- **Sabre and OAG one-off diagnostics**: `sabre_2023_control`, `sabre_cabin_diff`,
  `sabre_carrier_diff`, `sabre_compare_analyst`, `sabre_compare_exact`, `sabre_compare_refined`,
  `sabre_direction_check`, `sabre_factor_check`, `sabre_query_lhrsjc`
- **deck and workbook one-offs**: `make_explainer`, `make_genoa_deck`, `build_genoa_workbook`

**Nine entries on that list of 59 are test suites** and are not orphans at all: the audit cannot see
how they are invoked. `test_load_aci.py` reported 53 checks and none failed on 8 August. Do not
retire a test on the audit's say-so.

---

Avia Solutions Limited. All rights reserved.
