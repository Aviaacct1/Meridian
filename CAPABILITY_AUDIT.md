# Capability audit

Tree: `C:\AviaDev\app`

256 Python modules, by the name an import resolves to.

### Shadowed copies (4)

Same module name in more than one place. The shallower one wins on the import path and is the one audited; the other is listed here so it is never mistaken for the live file.

- `app_avia_style/cortex_app.py` is shadowed by `cortex_app.py`
- `app_avia_style/methodology_page.py` is shadowed by `methodology_page.py`
- `app_avia_style/route_engine.py` is shadowed by `route_engine.py`
- `app_avia_style/track_record.py` is shadowed by `track_record.py`

## 1. Nothing imports these

A module nothing imports is either a command-line tool, which is fine, or a capability with no way in, which is the `departure_time_grid.py` case.

### Command-line tools (104), expected to stand alone

`adjust_table`, `airport_fit`, `analyze_airport`, `analyze_calib`, `analyze_decomp`, `analyze_fare_elasticity`, `analyze_feed`, `analyze_induced`, `analyze_split`, `analyze_tail`, `analyze_tier`, `apd_experiment`, `assess`, `backtest`, `build_airport_capture`, `build_airport_capture_2way`, `build_airport_factors`, `build_business_case`, `build_cache`, `build_dot_enrichment`, `build_genoa_cache`, `build_hub_connectivity`, `build_hub_connectivity_region`, `build_master_backtest`, `build_od_fare`, `build_preagg`, `calib_bands`, `calib_feed_split`, `calib_interval`, `calib_market_trim`, `calib_share_trim`, `calib_split_share`, `calibrate_att_purpose`, `calibrate_catchment`, `calibrate_feed_qsi`, `calibrate_genoa`, `calibrate_share_att`, `calibrate_share_sweep`, `calibrate_sjc`, `calibrate_sjc_outturn`, `calibration_fit`, `calibration_library__6_`, `calibration_library_v7`, `calibration_model`, `catchment_master`, `catchment_trend`, `catchment_trend_ni`, `check_aci`, `check_airport`, `check_env`, `check_oag_grain`, `check_t100`, `city_pair_presentation`, `closed_loop_pipeline`, `closed_loop_pipeline_v2__1_`, `compare_airport_factor`, `compare_induced_fsc`, `compare_market_trim`, `compare_mct`, `compare_share_trim`, `departure_time_optimiser`, `diag_water_catchment`, `dir_split`, `explore_segments`, `fleet_check`, `genoa_nyc`, `ingest_all_oag`, `ingest_all_years`, `job_runner`, `ke_icn_sjc_update`, `leakage_diag`, `leakage_why`, `learning_comparison__1_`, `lopa_refresh`, `oag_drop_period`, `oag_ingest_periodic`, `oag_sweep_mistags`, `pipeline`, `pipeline__1_`, `pretest_qsi_discrimination`, `product_readout`, `qsi_forecast_tool`, `research_to_presentation`, `run_forecast`, `sabre_caribbean_check`, `sabre_generate_demand`, `sabre_generate_extract`, `sabre_generate_p2p`, `sabre_genoa_check`, `sabre_ingest`, `search_adjustments`, `seasonality_check`, `seasonality_from_monthly`, `sector_diag`, `test_cz_can_sjc`, `test_qsi_score`, `test_regression`, `test_regression_v2`, `test_route_case`, `test_route_forecast`, `validate_oag_load`, `validate_task_one`, `verify_identity`, `warm_demo`

### Neither imported nor runnable (59), CHECK EACH ONE

- `avia_dashboard.py`
- `avia_qsi_auto.py`
- `avia_qsi_auto_v3.py`
- `bench3.py`
- `bench4.py`
- `build_genoa_workbook.py`
- `direct_service_overlay.py`
- `importance2.py`
- `importance3.py`
- `improved_forecast.py`
- `make_explainer.py`
- `make_genoa_deck.py`
- `providers__1_.py`
- `providers_v2_fixed.py`
- `pull_airport_features.py`
- `pull_airport_features2.py`
- `pull_syd_per.py`
- `qsi_portal.py`
- `qsi_portal_v10.py`
- `qsi_portal_v11.py`
- `qsi_portal_v4.py`
- `qsi_portal_v8.py`
- `qsi_portal_v9.py`
- `raw_oag_provider.py`
- `route_assessment.py`
- `route_config_v2.py`
- `route_config_v3.py`
- `runner2.py`
- `runner3.py`
- `runner3b.py`
- `runner4.py`
- `runner4b.py`
- `sabre_2023_control.py`
- `sabre_cabin_diff.py`
- `sabre_carrier_diff.py`
- `sabre_compare_analyst.py`
- `sabre_compare_exact.py`
- `sabre_compare_refined.py`
- `sabre_direction_check.py`
- `sabre_factor_check.py`
- `sabre_query_lhrsjc.py`
- `scan_stores.py`
- `score2.py`
- `score3.py`
- `score4.py`
- `score_results.py`
- `segment_model.py`
- `stage_runner.py`
- `subgroups.py`
- `subgroups2.py`
- `test_airport_profile.py`
- `test_check_airport.py`
- `test_economics_wiring.py`
- `test_load_aci.py`
- `test_mct.py`
- `test_network.py`
- `test_qsi_feed.py`
- `test_research.py`
- `test_schedule_sizing.py`

## 2. Config keys read somewhere and set nowhere

A module that reads a key no file ever writes, and that is not a function argument either, is a capability that cannot be turned on. This is the `qsi_feed` and `dep_time_mins` case.

| Key | Read in | Written in |
|---|---|---|
| `provider_type` | `avia_qsi_auto.py` | nothing |
| `provider_type` | `avia_qsi_auto_v3.py` | nothing |
| `fy_capacity` | `backtest.py` | nothing |
| `summer_weeks` | `backtest.py` | nothing |
| `winter_weeks` | `backtest.py` | nothing |
| `n_routes` | `calibration_model.py` | nothing |
| `client_name` | `city_pair_pptx_generator.py` | nothing |
| `connecting_cities` | `city_pair_pptx_generator.py` | nothing |
| `client_name` | `city_pair_presentation.py` | nothing |
| `confidentiality` | `city_pair_presentation.py` | nothing |
| `demand_driver` | `city_pair_presentation.py` | nothing |
| `provider_type` | `closed_loop_pipeline_v2.py` | nothing |
| `provider_type` | `closed_loop_pipeline_v2__1_.py` | nothing |
| `capture_basis` | `cortex_workbook.py` | nothing |
| `china_connecting` | `ke_icn_sjc_update.py` | nothing |
| `demand_driver` | `narrative_generator.py` | nothing |
| `deck_title` | `pitch_report.py` | nothing |
| `route_flying_mins` | `qsi_feed.py` | nothing |
| `Aircraft Type` | `qsi_forecast_tool.py` | nothing |
| `Analyst` | `qsi_forecast_tool.py` | nothing |
| `Annual Seats` | `qsi_forecast_tool.py` | nothing |
| `Carrier` | `qsi_forecast_tool.py` | nothing |
| `Carrier IATA` | `qsi_forecast_tool.py` | nothing |
| `Date` | `qsi_forecast_tool.py` | nothing |
| `Destination Airport (IATA)` | `qsi_forecast_tool.py` | nothing |
| `Destination City` | `qsi_forecast_tool.py` | nothing |
| `Destination Country` | `qsi_forecast_tool.py` | nothing |
| `Forecast Year` | `qsi_forecast_tool.py` | nothing |
| `Frequency (per week)` | `qsi_forecast_tool.py` | nothing |
| `Mode` | `qsi_forecast_tool.py` | nothing |
| `Origin Airport (IATA)` | `qsi_forecast_tool.py` | nothing |
| `Origin City` | `qsi_forecast_tool.py` | nothing |
| `Origin Country` | `qsi_forecast_tool.py` | nothing |
| `Seats per Flight` | `qsi_forecast_tool.py` | nothing |
| `provider_type` | `qsi_portal_v10.py` | nothing |
| `provider_type` | `qsi_portal_v11.py` | nothing |
| `provider_type` | `qsi_portal_v4.py` | nothing |
| `provider_type` | `qsi_portal_v8.py` | nothing |
| `provider_type` | `qsi_portal_v9.py` | nothing |
| `file` | `raw_oag_provider.py` | nothing |
| `demand_driver` | `research_to_presentation.py` | nothing |
| `catchment_text` | `route_deck.py` | nothing |
| `full_report` | `route_deck.py` | nothing |
| `behind_cap` | `route_feed.py` | nothing |
| `dom_floor` | `route_feed.py` | nothing |
| `dom_gain` | `route_feed.py` | nothing |
| `blanks` | `test_load_aci.py` | nothing |
| `grain` | `test_load_aci.py` | nothing |
| `measure` | `test_load_aci.py` | nothing |

### Keys written by only one file

Not wrong, but worth a look: a switch only the back-test sets has never been used in production.

| Key | Only written by | Read elsewhere |
|---|---|---|
| `_qsi_fallbacks` | `route_feed.py` | `backtest` |
| `airport_data` | `research_to_presentation.py` | `narrative_generator` |
| `dep_time_mins` | `backtest.py` | `route_feed` |
| `flying_mins` | `backtest.py` | `route_feed` |
| `headline` | `narrative_generator.py` | `city_pair_pptx_generator` |
| `logit_lambda` | `backtest.py` | `qsi_feed` |
| `mct_banking` | `backtest.py` | `route_feed` |
| `qsi_feed` | `backtest.py` | `route_feed` |
| `qsi_k` | `backtest.py` | `route_feed` |
| `qsi_k_behind` | `backtest.py` | `route_feed` |
| `research` | `research_to_presentation.py` | `narrative_generator` |
| `route_freq` | `backtest.py` | `qsi_feed`, `route_feed` |
| `wave_cache` | `backtest.py` | `route_feed` |
| `why_points` | `narrative_generator.py` | `city_pair_pptx_generator` |

## 3. Data files named in code that are not in the tree

The 6 August failure: a loader opens a file by path, the file is not beside it, and the except returns a neutral value.

| File | Named in |
|---|---|
| `Airport_Database.xlsx` | `config.py`, `oag_parser.py`, `pipeline.py`, `pipeline__1_.py` |
| `Assumptions_Log_BA_LHR_SJC.json` | `assumptions_log.py` |
| `Assumptions_Log_BA_LHR_SJC.xlsx` | `assumptions_log.py` |
| `BALHR__SJC__XXX_Sep2013Aug2014_Fares_v2.xlsx` | `fare_allocation.py` |
| `BASJC__LHR__XXX_Sep2013Aug2014_FARES_v2.xlsx` | `fare_allocation.py` |
| `BA_LHR_SJC_Audit_Trail.txt` | `assembly_loop.py` |
| `BA_LHR_SJC_Fare_Allocation.xlsx` | `fare_allocation.py` |
| `BA_LHR_SJC_Forecast_Validated.xlsx` | `assembly_loop.py` |
| `BA_LHR_SJC_Standard_Output.xlsx` | `output_workbook.py` |
| `BA_LHR_SJC_business_case.xlsx` | `build_business_case.py` |
| `Bay_Area_Demandxlsx.xlsx` | `file_classifier.py` |
| `BusinessCase_BA_LHR_SJC.xlsx` | `business_case_mode.py` |
| `Business_Case.xlsx` | `build_business_case.py` |
| `CX_HKG_SJC_Research.json` | `city_pair_presentation.py`, `narrative_generator.py` |
| `Closed_Loop_BA_LHR_SJC.xlsx` | `closed_loop_pipeline.py` |
| `Closed_Loop_V2_BA_LHR_SJC.xlsx` | `closed_loop_pipeline_v2.py`, `closed_loop_pipeline_v2__1_.py` |
| `CrossRoute_Validation_Report.xlsx` | `avia_qsi_auto.py`, `avia_qsi_auto_v3.py`, `qsi_portal_v10.py`, `qsi_portal_v11.py`, `qsi_portal_v8.py` |
| `Cross_Route_Validation.xlsx` | `cross_route_validator.py` |
| `DepartureTimeOptimiser_BA_LHR_SJC.xlsx` | `departure_time_optimiser.py` |
| `DepartureTimeOptimiser_output.xlsx` | `departure_time_optimiser.py` |
| `IT.txt` | `test_route_case.py` |
| `LONSJCXXX.xlsx` | `file_classifier.py` |
| `LONSJCXXX_2013_data.xlsx` | `midt_demand_provider.py` |
| `Network_PnL.xlsx` | `network_report.py` |
| `OAGICN_AUG18.xlsx` | `ke_icn_sjc_update.py`, `route_config_v3.py` |
| `OAGSJC_Aug18.xlsx` | `ke_icn_sjc_update.py`, `route_config_v3.py` |
| `OAG_Airport__City_Lookup_DS_25Feb11.xlsx` | `config.py`, `file_classifier.py`, `oag_parser.py`, `pipeline.py`, `pipeline__1_.py` |
| `OAG_Parsed_LHR_SJC.xlsx` | `oag_parser.py` |
| `OAG__LHR__WORLD__LHR_AUG2014.xlsx` | `file_classifier.py`, `oag_parser.py`, `pipeline.py`, `pipeline__1_.py` |
| `OAG__SJC__WORLD__SJC_AUG2014.xlsx` | `oag_parser.py`, `pipeline.py`, `pipeline__1_.py` |
| `P2P_LONBAY_AREA_2013.xlsx` | `file_classifier.py`, `midt_demand_provider.py` |
| `Pipeline_BA_LHR_SJC.xlsx` | `pipeline.py`, `pipeline__1_.py` |
| `QSIAMS.xlsx` | `route_config_v2.py`, `route_config_v3.py` |
| `QSILHR.xlsx` | `file_classifier.py` |
| `QSILHR_v1_OS_JZ_17Feb15.xlsx` | `closed_loop_pipeline.py`, `departure_time_grid.py`, `file_classifier.py`, `input_validator.py`, `job_runner.py` |
| `QSILHR_v1_OS_JZ_5pm_dep_SJC_10Jun15.xlsx` | `departure_time_optimiser.py` |
| `QSILHR_v1_OS_JZ_new_time_05Mar15.xlsx` | `departure_time_optimiser.py` |
| `QSILHR_v1_OS_JZ_original_time_17Feb15.xlsx` | `departure_time_optimiser.py` |
| `QSISJC.xlsx` | `closed_loop_pipeline.py`, `departure_time_optimiser.py`, `input_validator.py`, `job_runner.py`, `pipeline.py` |
| `QSISJC_v1_5pm_dep_SJC.xlsx` | `departure_time_optimiser.py` |
| `QSISJC_v1_new_time.xlsx` | `departure_time_optimiser.py` |
| `QSI_CAN.xlsx` | `test_cz_can_sjc.py` |
| `QSI_Caibration_with_new_service_UK_Leisure_1.xlsx` | `file_classifier.py` |
| `QSI_SJC.xlsx` | `test_cz_can_sjc.py` |
| `QSI_Scorer_Validated.xlsx` | `qsi_scorer.py` |
| `QSI_Template_Blank.xlsx` | `qsi_forecast_tool.py` |
| `SJCLONXXX__2013_CUT_4_data.xlsx` | `file_classifier.py`, `midt_demand_provider.py` |
| `_audit.json` | `cortex_app.py` |
| `_config.json` | `city_pair_presentation.py` |
| `_enriched.json` | `research_to_presentation.py` |
| `_narrated.json` | `narrative_generator.py` |
| `_research_template.json` | `research_to_presentation.py` |
| `aci.duckdb` | `check_aci.py`, `config.py`, `load_aci.py`, `test_airport_profile.py`, `test_check_airport.py` |
| `aci_collide.duckdb` | `test_load_aci.py` |
| `aci_collide.xlsx` | `test_load_aci.py` |
| `aci_fixture.xlsx` | `test_load_aci.py` |
| `aci_full.duckdb` | `test_load_aci.py` |
| `aci_full.xlsx` | `test_load_aci.py` |
| `aci_test.duckdb` | `test_load_aci.py` |
| `assumptions.json` | `assumptions_log.py` |
| `assumptions.xlsx` | `assumptions_log.py` |
| `audit.txt` | `job_runner.py` |
| `avia_test_oag.duckdb` | `test_airport_profile.py` |
| `cache.json` | `routing.py` |
| `casm_benchmark.duckdb` | `config.py` |
| `catchments_qsi.json` | `catchment_master.py` |
| `config.json` | `job_runner.py` |
| `db1b.duckdb` | `config.py` |
| `demo_config.json` | `city_pair_presentation.py` |
| `form41_p12.duckdb` | `config.py` |
| `goa_drive.json` | `routing.py` |
| `input.json` | `job_runner.py` |
| `job.json` | `job_runner.py` |
| `oag.duckdb` | `calibrate_feed_qsi.py`, `config.py`, `oag_served.py`, `route_engine.py`, `test_check_airport.py` |
| `out.json` | `test_route_case.py` |
| `output.xlsx` | `job_runner.py`, `output_workbook.py` |
| `pipeline_oag.xlsx` | `pipeline.py`, `pipeline__1_.py` |
| `pptx_config.json` | `avia_qsi_auto.py`, `qsi_portal_v11.py` |
| `qa_checklist.xlsx` | `avia_qsi_auto.py`, `avia_qsi_auto_v3.py`, `qsi_portal_v10.py`, `qsi_portal_v11.py`, `qsi_portal_v8.py` |
| `qa_test.xlsx` | `qa_checklist.py` |
| `qsi2_state.pkl` | `runner2.py`, `score2.py`, `subgroups2.py` |
| `qsi3_state.pkl` | `runner3.py`, `score3.py` |
| `qsi3b_state.pkl` | `runner3b.py` |
| `qsi3c_state.pkl` | `bench3.py` |
| `qsi4_state.pkl` | `runner4.py`, `score4.py` |
| `qsi4b_state.pkl` | `runner4b.py` |
| `qsi4c_state.pkl` | `bench4.py` |
| `qsi_state.pkl` | `score_results.py`, `stage_runner.py` |
| `research_audit.json` | `cortex_app.py` |
| `results.json` | `job_runner.py` |
| `s.duckdb` | `catchment_master.py` |
| `s2.duckdb` | `catchment_master.py` |
| `sabre.duckdb` | `config.py`, `sector_diag.py` |
| `served_2025-05-26.json` | `oag_served.py`, `route_engine.py` |
| `store.duckdb` | `test_airport_profile.py` |
| `t100.duckdb` | `config.py`, `test_check_airport.py` |
| `test_seasonality.xlsx` | `seasonality_engine.py` |
| `there-is-no-t100-here.duckdb` | `test_check_airport.py` |
| `verify_identity_candidate.csv` | `verify_identity.py` |

Some will be outputs the tool writes rather than reads. Check the direction before acting.

## 4. Where failure is swallowed

Every one of the four capabilities lost this week failed inside one of these. A fallback is fine; a silent one is not.

234 swallowed handlers across 98 modules.

| Module | Count | Lines |
|---|---|---|
| `cortex_app.py` | 21 | 145, 152, 157, 379, 384, 611, 772, 799 |
| `backtest.py` | 13 | 299, 645, 658, 706, 711, 422, 438, 471 |
| `midt_demand_provider.py` | 10 | 444, 570, 578, 584, 269, 275, 281, 245 |
| `avia_qsi_auto_v3.py` | 9 | 210, 220, 231, 238, 128, 185, 692, 1993 |
| `airport_profile.py` | 7 | 530, 537, 314, 415, 495, 542, 591 |
| `route_forecast.py` | 7 | 427, 601, 640, 61, 457, 503, 565 |
| `avia_qsi_auto.py` | 6 | 157, 167, 174, 1969, 3203, 4331 |
| `catchment_master.py` | 6 | 626, 663, 946, 517, 579, 634 |
| `connection_builder.py` | 6 | 84, 238, 240, 79, 405, 441 |
| `pitch_verify.py` | 5 | 41, 54, 67, 156, 124 |
| `providers__1_.py` | 5 | 251, 258, 439, 443, 457 |
| `providers_v2_fixed.py` | 5 | 251, 258, 445, 449, 464 |
| `sabre_catchment.py` | 5 | 60, 98, 135, 167, 204 |
| `providers.py` | 4 | 252, 259, 434, 448 |
| `qsi_portal_v11.py` | 4 | 131, 1403, 2483, 3611 |
| `airfield_check.py` | 3 | 131, 282, 292 |
| `cre_pce_bridge.py` | 3 | 57, 66, 142 |
| `db_registry.py` | 3 | 103, 44, 122 |
| `fare_allocation.py` | 3 | 39, 266, 274 |
| `mct_bank.py` | 3 | 35, 61, 33 |
| `research_provider.py` | 3 | 116, 148, 208 |
| `route_engine.py` | 3 | 127, 95, 220 |
| `single_extract_oag_provider.py` | 3 | 245, 714, 479 |
| `warm_demo.py` | 3 | 117, 92, 163 |
| `analyze_fare_elasticity.py` | 2 | 35, 42 |

## 5. Environment variables the tool reads

Every one of these changes behaviour and none of them is visible in the tree. They belong in the README before the first commit.

- `ANTHROPIC_API_KEY` in `cortex_app.py`, `research_provider.py`
- `AVIA_ADJUDICATE_MODEL` in `research_provider.py`
- `AVIA_ALLOW_NO_WATER_CHECK` in `catchment_master.py`
- `AVIA_CASM_BENCHMARK` in `econ_benchmark.py`
- `AVIA_CONN_REGISTRY` in `db_registry.py`
- `AVIA_DB1B_DUCKDB` in `od_source.py`
- `AVIA_DECK_AUTHOR` in `city_pair_pptx_generator.py`, `pitch_report.py`
- `AVIA_DECK_SAFE_FONTS` in `pitch_report.py`
- `AVIA_DECK_STYLE` in `pitch_report.py`
- `AVIA_DECK_V4` in `pitch_report.py`
- `AVIA_DIAG_ORIGIN` in `diag_water_catchment.py`
- `AVIA_DIAG_YEAR` in `diag_water_catchment.py`
- `AVIA_DUCKDB_MEMORY` in `backtest.py`, `db_registry.py`
- `AVIA_DUCKDB_TEMP` in `backtest.py`, `db_registry.py`
- `AVIA_DUCKDB_THREADS` in `db_registry.py`
- `AVIA_ECON_FORM41` in `aircraft_economics.py`
- `AVIA_EGNYTE_ROOT` in `config.py`
- `AVIA_FREQ_DISCOUNT` in `route_forecast.py`
- `AVIA_FREQ_DISC_BETA` in `route_forecast.py`
- `AVIA_FREQ_DISC_CAP` in `route_forecast.py`
- `AVIA_FREQ_DISC_FLOOR` in `route_forecast.py`
- `AVIA_FREQ_DISC_REF` in `route_forecast.py`
- `AVIA_FRICTION` in `route_forecast.py`
- `AVIA_FRICTION_RASTER` in `catchment_master.py`
- `AVIA_GAF_SCREEN_LIST` in `catchment_master.py`
- `AVIA_GEONAMES` in `catchment_master.py`
- `AVIA_HAUL_LONG_BETA` in `route_forecast.py`
- `AVIA_HAUL_LONG_FLOOR` in `route_forecast.py`
- `AVIA_HAUL_SHORT_BETA` in `route_forecast.py`
- `AVIA_HAUL_SHORT_CAP` in `route_forecast.py`
- `AVIA_HAUL_SHORT_FLOOR` in `route_forecast.py`
- `AVIA_HAUL_TRIM` in `route_forecast.py`
- `AVIA_HAUL_TRIM_BETA` in `route_forecast.py`
- `AVIA_HAUL_TRIM_FLOOR` in `route_forecast.py`
- `AVIA_OAG` in `cortex_app.py`
- `AVIA_OD_SOURCE` in `od_source.py`
- `AVIA_PASSWORD` in `warm_demo.py`
- `AVIA_PROSE_MAX_TOKENS` in `pitch_prose.py`
- `AVIA_PROSE_MODEL` in `pitch_prose.py`
- `AVIA_QSI_BUILD` in `config.py`
- `AVIA_QSI_COMMIT` in `catchment_master.py`
- `AVIA_RESEARCH_MAX_BLOCKS` in `pitch_report.py`
- `AVIA_RESEARCH_MAX_FINDINGS` in `research_provider.py`
- `AVIA_RESEARCH_MAX_TOKENS` in `research_provider.py`
- `AVIA_RESEARCH_MODEL` in `research_provider.py`
- `AVIA_RESEARCH_PROVIDER` in `research_provider.py`
- `AVIA_RESEARCH_RELEVANCE` in `pitch_report.py`
- `AVIA_SABRE` in `cortex_app.py`, `diag_water_catchment.py`
- `AVIA_SABRE_YEAR` in `catchment_master.py`
- `AVIA_WATER_CHECK` in `water_check.py`
- `QSI_DEMO_ENTRY` in `cortex_app.py`
- `QSI_PASSWORD` in `cortex_app.py`

Copyright Avia Solutions Limited. All rights reserved.