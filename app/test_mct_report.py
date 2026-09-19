#!/usr/bin/env python3
"""Rule-lock for connection_builder.mct_report (John's ruling, 19 September 2026).

The point of the ruling is that a missing MCT master must never again be invisible.
These checks hold the three states apart, because they are three different faults and
the server's startup line has to name which one it is:

  missing   the file is not where config resolved it     -> exists False, rows 0
  unusable  the file is there and yields nothing         -> exists True,  rows 0
  loaded    the file is there and yields rows            -> exists True,  rows > 0

The last check records WHY any of this matters: with an empty MCT table every airport
takes the flat default, which is the silent behaviour the startup line now exposes.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import openpyxl
import connection_builder as CB

CHECKS = []


def check(name, got, want):
    ok = got == want
    CHECKS.append((name, ok, got, want))
    return ok


def _write_mct_workbook(path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Airport", "TermArr", "TermDep", "DomInt", "Minutes"])
    ws.append(["LHR", 2, 5, "INT", 90])     # keyed with and without terminals: 2 entries
    ws.append(["JFK", None, None, "DOM", 60])  # no terminals: 1 entry
    wb.save(path)
    wb.close()


def main():
    tmp = tempfile.mkdtemp(prefix="mct_report_")

    # 1. MISSING: the file is not there at all.
    missing = os.path.join(tmp, "not_here.xlsx")
    r = CB.mct_report(missing)
    check("missing: exists is False", r["exists"], False)
    check("missing: rows is 0", r["rows"], 0)
    check("missing: no error, absence is not a parse failure", r["error"], None)
    check("missing: path is echoed so the message can name it", r["path"], missing)

    # 2. LOADED: a real workbook yields rows.
    good = os.path.join(tmp, "MCT Master List.xlsx")
    _write_mct_workbook(good)
    r = CB.mct_report(good)
    check("loaded: exists is True", r["exists"], True)
    check("loaded: no error", r["error"], None)
    check("loaded: three keys from two rows", r["rows"], 3)

    # 3. UNUSABLE: the file is there and gives up nothing. Not the same fault as missing.
    bad = os.path.join(tmp, "broken.xlsx")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write("this is not a workbook")
    r = CB.mct_report(bad)
    check("unusable: exists is True", r["exists"], True)
    check("unusable: rows is 0", r["rows"], 0)

    # 4. NO ARGUMENT: resolves through config and must not raise, whatever the machine holds.
    try:
        r = CB.mct_report()
        check("default: returns a dict", isinstance(r, dict), True)
        check("default: reports a path", isinstance(r["path"], str), True)
        check("default: never raises", True, True)
    except Exception as e:                                       # noqa: BLE001
        check("default: never raises", "raised %s" % type(e).__name__, True)

    # 5. WHY IT MATTERS: an empty table sends every airport to the flat default, silently.
    check("empty table falls to the default connect time",
          CB.lookup_mct({}, "LHR", "2", "5", "INT", default_mct=90), 90)
    loaded = CB.load_mct_data(good)
    check("a loaded table answers from the table, not the default",
          CB.lookup_mct(loaded, "JFK", "", "", "DOM", default_mct=90), 60)

    failed = [c for c in CHECKS if not c[1]]
    for name, ok, got, want in CHECKS:
        if not ok:
            print("FAIL  %s: got %r, wanted %r" % (name, got, want))
    print("%d checks, %d failed" % (len(CHECKS), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
