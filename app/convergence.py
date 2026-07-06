#!/usr/bin/env python3
"""
Avia Solutions - load-factor convergence helper.
=================================================
Non-invasive. This does NOT change the calibrated pipeline. It runs the
pipeline, then scales the QSI adjustment so the forecast lands at a target
load factor - the iterative step analysts apply by hand to pull a raw QSI
capture (which can imply a 150-175% load factor) back to a plausible level.

The grand total is exactly linear in qsi_adjustment, because P2P demand is
fixed and only connecting capture scales with it. So the convergence solves in
one step rather than iterating: measure the raw connecting at adjustment 1.0,
then set adjustment = (target_total - P2P) / raw_connecting.

Scope. This is a BACK-TEST tool, for routes whose achieved load factor is
known (the BA LHR-SJC reference case, the 70 historic forecasts). Forecasting a
brand-new route cannot assume a known target load factor; there the convergence
must come from a calibration factor derived from the data (comparing pipeline
QSI against a market QSI reference), which is a separate method question to
settle with the analyst.
"""

import io
import contextlib


def _run_quiet(config):
    from closed_loop_pipeline_v2 import run_pipeline
    with contextlib.redirect_stdout(io.StringIO()):
        return run_pipeline(config)


def converge_to_load_factor(config, target_lf):
    """Scale qsi_adjustment so the forecast lands at target_lf.

    Returns (results, qsi_adjustment). Mutates config.qsi_adjustment.
    """
    capacity = config.annual_capacity
    if capacity <= 0:
        raise ValueError("config.annual_capacity must be positive")

    # Baseline at adjustment 1.0 to read the raw (unscaled) connecting demand.
    config.qsi_adjustment = 1.0
    base = _run_quiet(config)
    p2p = base["p2p_total"]
    raw_connecting = base["grand_total"] - p2p
    if raw_connecting <= 0:
        return base, 1.0

    target_total = target_lf * capacity
    adjustment = (target_total - p2p) / raw_connecting
    config.qsi_adjustment = adjustment
    results = _run_quiet(config)
    return results, adjustment


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from route_config import RouteConfig
    cfg = RouteConfig.ba_lhr_sjc()
    res, adj = converge_to_load_factor(cfg, 0.829)
    cap = cfg.annual_capacity
    print(f"converged adjustment = {adj:.4f}")
    print(f"grand total = {res['grand_total']:,.0f}  (target 129,162)")
    print(f"load factor = {res['grand_total'] / cap:.1%}  (target 82.9%)")
