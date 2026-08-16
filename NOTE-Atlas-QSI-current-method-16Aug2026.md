# The QSI element of Atlas: moving to the current Meridian methodology

Note for the Atlas build chat. Version 1.0, 16 August 2026. Avia Solutions.

Written from the Meridian side in response to the Atlas independent review of 16 August
2026, whose route-module findings concern the QSI / BT2 element that Atlas wired into
the BUM on 5 August (CHANGELOG 87, 89, 90). The review's direction is right: the
client-facing surface must describe the model as it ships. Its QSI figures, however,
predate three weeks of movement in the Meridian programme, and the wording finding runs
into a ruling John has already made. This note gives the current state, the file that
carries each figure, and the process changes to make. Verify every number against
`bt2/bt2_experiments.log` and `bt2_claimset.py` in the meridian repo before it drives
copy; nothing below should be taken on this note's authority alone.

## 1. The audit's figures are stale, in both directions

The review quotes blind 54% against a calibrated headline of 89%, and 94% within
plus or minus 20% on twenty-route portfolios.

- **The blind single-route control is 55.9%**, not 54%: leave-one-launch-year-out,
  n=3,700, launch years 2016-2019 plus 2024 and 2025, G12 features, set 9 August
  (`bt2_experiments.log`). Anything quoting 51%, 53% or 54% as "BT2 blind" is stale.
  No further launch years can ever be built: the OAG store covers 2015-2019 and
  2023-2026 only, so 2024 was the last.
- **The calibrated headline is 88.8% within plus or minus 20% and 82.4% within 10%,
  n=2,915**, on the mixed grading basis that followed the US grading rule (US routes
  graded against DB1B, not Sabre). A surface quoting 89.8% predates that re-score.
  The published basis is `app/master_backtest_scored.csv`; the model configuration
  behind it is pinned in `bt2_claimset.py`.
- **The twenty-route portfolio figure stands**: 94.3% on the 2025 forward test, 95.4%
  pre-COVID; portfolios of ten 80.0% forward, 81.3% pre-COVID. This is the strong
  blind evidence and it is already the quotable form.

## 2. The wording finding, and the ruling that already governs it

The review proposes making the blind figure the headline. That collides with John's
5 August claim-language ruling, applied repo-wide at the time and binding on both
products: lead with calibrated 88.8 / 82.4 plus the distribution chart; blind evidence
appears second and ONLY as portfolios (80% of ten-route baskets, 94% at twenty);
single-route blind figures never appear in client material, model card and changelog
only. The load-bearing words are "calibrated" and "unseen", and neither may borrow the
other's number.

The review's real finding therefore is not that the headline is the wrong number; it is
that the Atlas surface let "calibrated" read as though it meant unseen. The remedy is
the ruling's wording discipline on the page, with the basis stated beside the figure,
not a swap of headline for blind. The covering summary itself puts the final wording
with John, and that stands: put the current wording and the ruling's wording side by
side for his decision before he leaves, and change nothing client-facing until he rules.

## 3. What has moved in the methodology since the 5 August wiring

- **Model artefact**: `bt2_model_v1_2.pkl` with `forecast_v12()` and the five G12 route
  keys (base_seats_a/b, airport_seats_a/b, sister_flag) supersedes v1.0 and v1.1.
  Confirm which artefact the BUM actually loads; a version bump was flagged to your
  chat on 5 August. Re-run your own three-airport ratio check after any bump; that
  check found the v1.0 wiring fault and is worth keeping as a hard fail.
- **The segment rule** now beats the IQR confidence tier as the product shape, because
  the split is known entirely in advance and a client can check it: short-haul under
  2,500 km, domestic or LCC, 70.4% blind within plus or minus 20% (n=1,432);
  long-haul international full-service 36.5% (n=1,090). Confidence over 60% blind
  already exists on 39% of launches. Tier-A thresholds are era-sensitive across COVID
  and ship as a confidence band only, never as a headline.
- **US grading rule**: US-domestic routes are trained and graded against DB1B; where
  Sabre and DOT disagree, DOT wins. The outturn source is a named column in the
  evidence file. 2025 US routes stay Sabre-graded and flagged until the DB1B 2025
  quarters land.
- **Growth at route level**: the 15 August ruling is the 2015-2019 pre-COVID trend,
  measured on the two-way pair sum, thin pairs refusing to a named assumed 3%. Never
  a post-COVID rebound CAGR: the rebound read as a rate compounded a below-peak pair
  to 22% above peak within three years, which is how three acceptance runs were
  misread. Related store fact: Sabre 2013 and 2015 are point-of-origin, all other
  years are nondirectional, so never measure cross-year growth one-directional across
  the 2015/2016 boundary (`app/sabre_directionality_check.py`).
- **One model, and the control arm.** Meridian closed its own version of Atlas's
  problem on 15 August: the evidence machine and the product are now the same machine
  (V1 carries the connecting level, V2 keeps the timing), and the shipped
  configuration has its own reference arm, `bt_v1_control.csv`, rendered on the track
  record page as "The engine as shipped" with both bases named. That is the pattern
  for the Atlas accuracy card: a control arm run through the shipped configuration,
  loaded by its own loader so a correction already inside the arm is not applied
  twice, and the basis of every figure named on the page it appears on.
- **A population trap to avoid in copy**: the relaxed discovery sample (n=6,524,
  blind 60.9%) is a second population, not a better model; the paired test on the
  overlap is p=0.330. Quoting it against the canon sample would be the exact
  calibrated-versus-unseen borrowing the ruling forbids.

## 4. The process changes, in order

1. Confirm the BUM loads `bt2_model_v1_2.pkl` via `forecast_v12()`; bump if not, then
   re-run the three-airport ratio check and your validation suite.
2. Pull the meridian repo rather than carrying private copies of any BT2 artefact or
   claim file. Git is the single source of truth under the tool standard; the split
   the review found is what stale copies produce.
3. Rebuild the accuracy card from the model's own artefacts: calibrated 88.8 / 82.4
   (n=2,915) with the distribution chart, blind portfolios 80 / 94 second, the basis
   named beside each figure, single-route blind figures nowhere on the surface. The
   schedule-test card the review flagged comes down; the real backtests replace it.
4. Take the wording decision to John before 26 August with both texts in front of him.
5. Adopt the segment rule as the confidence shape on route output; tier-A only as a
   band.
6. Apply the US grading rule wherever Atlas grades or displays US-domestic route
   accuracy, with the outturn source named.
7. Any route-level growth Atlas states follows the pre-COVID trend ruling and the
   directionality rule above.
8. Carry Meridian's refusal rule: a warned run renders on a portal with the warning
   stated, and is refused for any client artefact. If the Atlas route module surfaces
   a run that carries warnings, the export refuses with the reason.

Settled items, do not re-open without new measurement: the calibrated-headline basis
(John, 6 August), the k decision and level/timing split (15 August), and the items
closed by measurement in `bt2_experiments.log` on 9 August (fare conditioning,
departure-time quality, size calibration, the regularisation retune).

For the October joint demo, Meridian itself is live at meridian.aviacortex.com behind
Cloudflare Access, serving /api/forecast and the forecast pack; if Atlas wants
route-level product served rather than re-modelled, that service is the join, not a
code copy.

Sources: `bt2/bt2_experiments.log`, `bt2_claimset.py`, `app/master_backtest_scored.csv`,
`QSI_SITE_ACCURACY_COPY.md`, `app/methodology_page.py`, `app/sabre_directionality_check.py`,
`bt_v1_control.csv` and `track_record.py` (all meridian repo); figures restated from the
Meridian project record of 5-16 August 2026.

Avia Solutions Limited. All rights reserved.
