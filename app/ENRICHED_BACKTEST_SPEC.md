# Enriched backtest substrate — spec for continuous multivariate calibration

**Author:** Avia Solutions
**Date:** 9 July 2026
**Goal:** one frozen, feature-rich backtest file we can run grouped cross-validated experiments on repeatedly, to model per-airport/route bias as a **function of characteristics** (few coefficients, all airports) rather than a free factor per airport. Target: hold circa 52% full-data fit **and** lift accuracy on unseen routes above the current 41%, by keeping fit and live close the way a proper regression does.

## Why this and not the free factor
A free factor per airport is under-determined (one number, 6-15 routes) so its fit overstates live accuracy; every out-of-sample test we ran landed flat to slightly negative. A correction keyed on real characteristics (secondary-vs-primary, catchment overlap, haul, carrier type) is over-determined and generalises. The substrate below is what lets us fit and validate that version, and every finer segmentation you named (intl/dom, intl inbound vs outbound) becomes a column to slice, not a new model.

## Substrate: one row per gradeable launch route-year
**Identity:** dep, arr, year, carrier, launch_id
**Outcome:** forecast_pax, outturn_pax, fc_over_out, p2p_outturn, connecting_outturn, captured, feed, natural
**Decomposition legs (already produced by `backtest --decompose`):** d_mkt_asif, d_mkt_outturn, d_growth_applied, d_share, d_dshare, d_stim, d_coverage, d_captured, d_feed_fc, d_cap_bound, L_market, L_capture
**Route features (forecast-time, no leakage):**
- domestic_intl (country[dep] vs country[arr])
- direction relative to the focus airport (inbound / outbound)
- haul_band from great-circle distance (short < 1500 km, medium 1500-4000, long > 4000)
- market_size_band (measured Sabre O&D)
- nonstop_share, competition_count, contested flag
- region[dep], region[arr], partner_region
- capacity_bound flag, qsi_share, dshare, stim

**Airport-attributes table (the missing piece — join on dep and on arr):**
- metro/city, primary_secondary (is it the secondary in a multi-airport metro?)
- catchment_overlap (share of catchment shared with a larger nearby airport)
- hub_type / transfer_share
- lat, long, country
- runway length / elevation capability

**Carrier attributes:** type (FSC / LCC / ULCC / charter), home-carrier flag

## Two data dependencies (these gate everything)
1. **Extend the backtest to 2025, and 2026-partial if Sabre 2026 exists.** Single most valuable addition: it roughly doubles same-regime (post-COVID) held-out volume and enables the fit-2024 / apply-2025 test that actually settles the per-airport question. **John kicks this** (py-3.12 engine run, `--decompose`).
2. **Airport-attributes table.** Most of it we can assemble from assets already built:
   - hub_type / transfer_share — from the hub-connectivity / region_localness work (built)
   - runway / elevation — from the airfield-performance layer (built)
   - catchment_overlap + primary_secondary — from the validated catchment cell-data (the only genuinely new designation to make per airport)
   - lat / long / country — confirm we hold an airport reference (OAG ref or OurAirports)
   **Claude builds this** on your word, flagging any source we don't yet hold.

## Validation protocol the substrate must support (build the keys in)
- grouped cross-validation **by airport** (a route never sits in the fold that sets its own airport's coefficient)
- held-out **year**: fit ≤ 2024, grade 2025, inside the post-COVID regime
- per-segment reporting: dom/intl, inbound/outbound, haul, size, carrier type
- always report **both** the full-data fit and the grouped/held-out figure, and show the gap

## Next actions
- **John:** kick the 2025 (+2026-partial) backtest with `--decompose`; confirm Sabre 2026 availability. Output alongside bt_v2 as `bt_v3_2025.csv`.
- **Claude:** build (a) the airport-attributes assembly from existing assets, (b) the enrichment/join script that turns a raw backtest into this substrate, (c) the multivariate grouped-CV harness that fits the characteristic-based bias model and reports full-data plus held-out per segment.
