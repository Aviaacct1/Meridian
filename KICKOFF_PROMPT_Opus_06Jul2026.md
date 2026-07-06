# Kick-off prompt for the first Opus chat (paste the block below as the opening message)

---

You are taking over development of the Avia Cortex QSI route-forecasting tool for the next few
weeks, working towards a live offline demo at World Routes in late September. Your working
brief is **REVIEW_QSI_for_Opus_05Jul2026.md** in the project root - read it in full before
doing anything, together with the memory notes (start with qsi-review-for-opus and
qsi-engine-v2). The review's ordered fix list IS the plan; do not re-derive it.

Decisions already settled - do not re-litigate: the V2 schedule-quality QSI feed beat V1 on
six years of matched launches including the untuned years (2016 +.118, 2024 +.080), so V2
becomes the default engine inside the Phase 5 bundle with k=0.65, k_behind=1.41, lambda=0.5
(re-solve k after the P2P level trim). Lambda was gridded 0.5-2.0; sharpening always lost.
The baselines to compare against are bt_v1_6yr.csv and bt_v2_6yr.csv on the pinned set
pinned_6yr_v2.json.

Your first milestone is RUNTIME, not modelling (review items 1-3): move the pin-bypass check
above discovery, replace per-query DuckDB connection churn with a per-process registry, build
the Sabre pre-aggregation tables (od_pairs, conn_markets, and the leg-exploded adjacency table
for sector_traffic), then add a multiprocessing route pool with week-grouped chunks. Build the
verification harness FIRST: a script that runs backtest --limit 100 on pinned routes and diffs
the output rows against the same routes in bt_v1_6yr.csv - every value identical, because
these are pure performance changes. Target: a full run under one hour. Do not touch model
behaviour in the same commits.

Second milestone: the demo hardening batch (items 4-8) - local non-OneDrive deployment with a
pinned venv and requirements.txt, warm_demo.py per the review's spec, resolution chips and
retired-IATA aliases, the confidence band and tile hierarchy on the result card, CRE sanity
rails.

Third: the ONE calibration run (item 9) - the Phase 5 bundle exactly as specified, compared
against both baselines, by-year and by-bucket. Only after that lands do you consider anything
else on the list.

Hard rules, learned expensively: never spend a full run on anything a --limit 100 identity
check can verify; never let two model changes share one run without an attribution plan (see
the k=0.06 artefact in the memory notes); level the feed before reading dispersion in any
compare; all engine changes opt-in behind flags until their back-test passes; bucket
corrections only as capped factors and only when two independent year-groups agree. The
OneDrive-synced folder can serve stale file views to tooling - verify on the real machine, and
never run the demo from it.

Report progress against the fix-list numbering. When in doubt about intent, the review and the
memory notes are the record; John decides anything they don't settle.

---
