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
    p.add_argument("--allow-warnings", action="store_true",
                   help="write a contract even when the forecast payload carries warnings. "
                        "By default a warned run is REFUSED: a deck must never be built on a "
                        "crashed feed layer, a silent V1 fallback or an empty departure board, "
                        "and John's 15 August ruling is refuse here, warn on the portal.")
    return p.parse_args()


def _blocks(contract):
    """How FULL each block is, and the named gaps with the reason deck_contract gave.

    THE FIRST VERSION OF THIS COUNTED A BLOCK AS FULL IF ANY ONE FIELD WAS POPULATED, so a block
    with one field of twenty read as complete and the report said "0 empty" on every case. That is
    a test that cannot fail, on the one screen whose whole purpose was to show where the gaps are.

    Now it returns the fill ratio per block and every missing key, with the sibling _need note
    deck_contract writes to say WHY a field is empty. The _need notes are the actionable part: they
    name what the model does not yet produce, which is the list of tables to populate.
    """
    out = {}
    for k, v in sorted(contract.items()):
        if k.startswith("_") or k == "currency":
            continue
        if isinstance(v, dict):
            keys = [kk for kk in v if not kk.startswith("_")]
            gaps = []
            for kk in keys:
                if v[kk] in (None, "", [], {}):
                    # THREE NAMING CONVENTIONS, and the first version knew two of them.
                    # deck_contract writes _rows_need, _origin_city_need and _schedule_times_need,
                    # so the leading underscore form is the common one and it was the one missed.
                    # The reason for the last empty block was therefore being swallowed by the
                    # report written to show it.
                    gaps.append((kk, v.get("_%s_need" % kk) or v.get("_need_" + kk)
                                 or v.get(kk + "_need") or v.get("_need") or ""))
            out[k] = (len(keys) - len(gaps), len(keys), gaps)
        elif isinstance(v, list):
            out[k] = (len(v), len(v) or 1, [] if v else [("(no rows)", "")])
        else:
            ok = v not in (None, "")
            out[k] = (1 if ok else 0, 1, [] if ok else [(k, "")])
    return out


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
        # "segments" is legitimate here and unknown to scenario_runner, which only forecasts.
        unknown = sorted(set(case) - SR.CASE_KEYS - {"segments"})
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
            # A WARNED RUN DOES NOT BECOME A DECK. The payload's warnings list is empty on a
            # clean run; anything in it means a number was not produced the way the page
            # will claim it was. The portal renders a warned run with the warning stated;
            # a contract is a client artefact and is refused instead.
            _warns = fc.get("warnings") or []
            if _warns and not a.allow_warnings:
                raise RuntimeError("forecast carries warnings and --allow-warnings is not "
                                   "set: " + "; ".join(str(w) for w in _warns))
            # "segments" carries the eight-segment judgement inputs and is the one case key that is
            # NOT a forecast setting, so it is passed to the contract rather than to the engine.
            contract = contract_from_forecast(fc, currency=a.currency,
                                              segments=case.get("segments"))
        except Exception as e:                               # noqa: BLE001
            failed.append((name, "%s: %s" % (type(e).__name__, e)))
            print("  %-52s FAILED  %s" % (name[:52], e))
            continue

        blocks = _blocks(contract)
        for bk, (have, tot, gaps) in blocks.items():
            rec = seen_thin.setdefault(bk, {"have": 0, "tot": 0, "n": 0, "why": {}})
            rec["have"] += have; rec["tot"] += tot; rec["n"] += 1
            for gk, why in gaps:
                rec["why"][gk] = why or rec["why"].get(gk, "")
        _eng = (fc.get("forecast_engine") or {}).get("local_leg", "?")
        _h = sum(b[0] for b in blocks.values()); _t = sum(b[1] for b in blocks.values())
        print("  %-52s %-16s %d of %d fields carry a figure (%.0f%%)"
              % (name[:52], _eng, _h, _t, 100.0 * _h / max(_t, 1)))
        if a.out and not a.report_only:
            stem = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)[:80]
            p = os.path.join(a.out, stem + "_contract.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(contract, fh, indent=2, default=str)
            try:
                import deck_contract as DC
                DC.emit_workbook(contract, os.path.join(a.out, stem + "_contract.xlsx"))
            except Exception as e:                           # noqa: BLE001
                # THE LINE, NOT JUST THE KEY. A bare KeyError name cost three round trips on 13
                # August: 'base_annual_demand', then 'nr', then 'annual_demand', each one guessed
                # at from the key alone when the traceback knew exactly which line raised it.
                import traceback
                tb = traceback.extract_tb(e.__traceback__)
                where = tb[-1] if tb else None
                print("       workbook not written: %s: %s" % (type(e).__name__, e))
                if where:
                    print("       at %s line %d: %s" % (os.path.basename(where.filename),
                                                        where.lineno, (where.line or "").strip()[:100]))

    if seen_thin:
        print("\nHOW FULL EACH BLOCK IS, across every case. THE LIST OF TABLES TO POPULATE is the")
        print("bottom of this table, not the top: deck_contract emits a gap as None with a _need")
        print("note rather than a zero, so an empty field is visible instead of reading as a")
        print("measurement of nothing.")
        print("\n   %-30s %8s  %s" % ("block", "filled", "fields with no figure"))
        for k, rec in sorted(seen_thin.items(), key=lambda kv: kv[1]["have"] / max(kv[1]["tot"], 1)):
            pc = 100.0 * rec["have"] / max(rec["tot"], 1)
            gaps = sorted(rec["why"])
            print("   %-30s %7.0f%%  %s" % (k, pc, ", ".join(gaps[:6]) + (" ..." if len(gaps) > 6 else "")
                                            or "none"))
        _why = {g: w for rec in seen_thin.values() for g, w in rec["why"].items() if w}
        if _why:
            print("\n   WHY, in deck_contract's own words:")
            for g, w in sorted(_why.items()):
                print("     %-26s %s" % (g, w[:100]))
    if failed:
        print("\n%d case(s) did not produce a contract:" % len(failed))
        for n, why in failed:
            print("   %-46s %s" % (n[:46], why))
    print("\n%s" % ("reported only, nothing written" if a.report_only
                    else ("wrote to %s" % a.out) if a.out else "no --out given, nothing written"))


if __name__ == "__main__":
    main()
