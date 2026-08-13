"""Run a cases file and emit a deck data contract per route, with a report of what populated.

    py -3.12 deck_from_cases.py cases_sjc_tpe.json --out E:\\Avia\\contracts

One command, the same cases file scenario_runner takes, so the numbers in a deck and the numbers in
the scenario table come from one definition of the case rather than from two. Every figure comes
from cortex_app.calibrated_forecast and is mapped by forecast_to_contract; nothing here computes a
forecast and nothing here writes a slide.

WHY THE REPORT MATTERS MORE THAN THE CONTRACT TONIGHT. deck_contract emits fields the model does not
produce as None with a sibling _need note, so the deck degrades gracefully and the gaps are
explicit. That is the right design and it means a contract can be complete-looking and thin. This
prints, per case, which blocks carry figures and which are empty, so the tables that need populating
are a list rather than a discovery halfway through building a deck.

    py -3.12 deck_from_cases.py cases_sjc_tpe.json --report-only

runs everything and writes nothing, which is the fastest way to see where the gaps are.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def parse_args():
    p = argparse.ArgumentParser(description="A deck data contract per case, from the live forecast.")
    p.add_argument("cases", help="a cases JSON with a defaults block and a cases list")
    p.add_argument("--out", default=None, help="folder for the contract JSON and workbook per case")
    p.add_argument("--currency", default="USD",
                   help="stated, never inferred: the contract carries fares without a currency and "
                        "guessing puts the wrong symbol on every revenue figure")
    p.add_argument("--report-only", action="store_true", help="run and report, write nothing")
    return p.parse_args()


def _blocks(contract):
    """Which top-level blocks carry a figure and which are empty, by the contract's own convention:
    a value is a gap when it is None, and deck_contract marks the reason in a sibling _need key."""
    full, thin = [], []
    for k, v in sorted(contract.items()):
        if k.startswith("_") or k == "currency":
            continue
        if isinstance(v, dict):
            vals = [x for kk, x in v.items() if not kk.startswith("_")]
            have = sum(1 for x in vals if x not in (None, "", [], {}))
            (full if have else thin).append("%s (%d of %d)" % (k, have, len(vals)))
        elif isinstance(v, list):
            (full if v else thin).append("%s (%d rows)" % (k, len(v)))
        else:
            (full if v not in (None, "") else thin).append(k)
    return full, thin


def main():
    a = parse_args()
    if not os.path.exists(a.cases):
        sys.exit("cases file not found: %r" % a.cases)

    # AVIA_FREQ_SENSITIVE is refused rather than defaulted, the same rule scenario_runner applies:
    # without it a route returns the same demand at 3x and at 14x and only the load factor moves,
    # so a deck would show a frequency ladder that is not one.
    if os.environ.get("AVIA_FREQ_SENSITIVE", "").strip() not in ("1", "true", "on", "yes"):
        sys.exit("AVIA_FREQ_SENSITIVE is not set. A deck built without it shows a frequency ladder "
                 "that does not respond to frequency. Set it to 1 and rerun.")

    import cortex_app as CA
    import scenario_runner as SR
    from forecast_to_contract import contract_from_forecast, case_and_outputs

    with open(a.cases, encoding="utf-8") as f:
        blob = json.load(f)
    defaults = blob.get("defaults") or {}
    cases = blob.get("cases") or []
    print("%s: %d case(s)" % (os.path.basename(a.cases), len(cases)))
    print("engine switch: %s\n" % (os.environ.get("AVIA_FORECAST_ENGINE") or "qsi (default)"))

    if a.out and not a.report_only:
        os.makedirs(a.out, exist_ok=True)

    seen_thin, failed = {}, []
    for i, raw in enumerate(cases, 1):
        case = dict(defaults); case.update(raw)
        name = case.get("name") or "case %d" % i
        unknown = sorted(set(case) - SR.CASE_KEYS)
        if unknown:
            failed.append((name, "unknown setting(s): " + ", ".join(unknown)))
            print("  %-52s SKIPPED  unknown setting(s) %s" % (name[:52], ", ".join(unknown)))
            continue
        kw = dict(airline=(case.get("airline") or None),
                  carrier_type=(case.get("carrier_type") or "FSC"),
                  aircraft=(case.get("aircraft") or "A21X"),
                  freq=SR._num(case.get("freq"), 7), seats=SR._num(case.get("seats")),
                  plan_lf=SR._num(case.get("plan_lf"), 0.875, cast=float),
                  split_floor=SR._bool(case.get("split_floor"), True),
                  season=(case.get("season") or "annual").strip().lower(),
                  partner_carriers=(SR._partners(case.get("partners")) or None),
                  dep_time_mins=SR._mins(case.get("dep_time")), with_econ=True)
        if SR._num(case.get("forecast_year")):
            kw["forecast_year"] = SR._num(case["forecast_year"])
        _g = SR._growth(case.get("growth"))
        if _g is not None:
            kw["growth"] = _g
        try:
            fc = CA.calibrated_forecast(case["origin"], case["dest"], **kw)
            contract = contract_from_forecast(fc, currency=a.currency)
        except Exception as e:                               # noqa: BLE001
            failed.append((name, "%s: %s" % (type(e).__name__, e)))
            print("  %-52s FAILED  %s" % (name[:52], e))
            continue

        full, thin = _blocks(contract)
        for t in thin:
            seen_thin[t.split(" (")[0]] = seen_thin.get(t.split(" (")[0], 0) + 1
        _eng = (fc.get("forecast_engine") or {}).get("local_leg", "?")
        print("  %-52s %-16s %d blocks with figures, %d empty"
              % (name[:52], _eng, len(full), len(thin)))
        if a.out and not a.report_only:
            stem = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)[:80]
            p = os.path.join(a.out, stem + "_contract.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(contract, fh, indent=2, default=str)
            try:
                import deck_contract as DC
                DC.emit_workbook(contract, os.path.join(a.out, stem + "_contract.xlsx"))
            except Exception as e:                           # noqa: BLE001
                print("       workbook not written: %s" % e)

    if seen_thin:
        print("\nBLOCKS CARRYING NO FIGURES, and how many cases each was empty on. This is the list")
        print("of tables to populate, not a list of faults: deck_contract emits a gap as None with")
        print("a _need note rather than a zero, so a thin block is visible instead of misleading.")
        for k, n in sorted(seen_thin.items(), key=lambda kv: -kv[1]):
            print("   %-34s empty on %d case(s)" % (k, n))
    if failed:
        print("\n%d case(s) did not produce a contract:" % len(failed))
        for n, why in failed:
            print("   %-46s %s" % (n[:46], why))
    print("\n%s" % ("reported only, nothing written" if a.report_only
                    else ("wrote to %s" % a.out) if a.out else "no --out given, nothing written"))


if __name__ == "__main__":
    main()
