#!/usr/bin/env python3
r"""The scoring band, in one place, with a self-test. Written 9 August 2026 after two failures.

    python3 bt2_score.py        runs the self-test

WHY THIS EXISTS, and it is not a tidy-up. On 9 August 2026 the scoring basis drifted twice in one
session, in two different files, both times silently and both times only caught because a control
figure looked unfamiliar:

  bt2_mix_exp     scored |log(f/A)| <= log(1.2), the ratio band 0.833 to 1.20. Symmetric in logs,
                  tighter on the low side. Read the control at 51.3% against its true 55.9%
  bt2_objective   scored log(f/A) in [-log(1.2), +log(1.25)], which is the correct band INVERTED:
                  wide above instead of wide below. Read the control at 54.2%, and made a derived
                  shift appear to point the wrong way

Both comparisons were internally valid, because each scored its control and its arm the same way.
Neither set of levels could be placed beside any other number in the programme. That is the exact
failure the accuracy work keeps guarding against elsewhere, arriving through the back door.

THE BAND, once, and nothing else may restate it.

    a hit is  |f/A - 1| <= 0.20,  so  f/A in [0.80, 1.20]

    in logs, with e = log(f/A):   e in [log 0.80, log 1.20] = [-0.22314, +0.18232]

    WIDER BELOW THAN ABOVE. Being 20% under the outturn is a longer step in logs than being 20%
    over it, so the window's midpoint is -0.02041 and not zero. Any argument about where to place a
    forecast inside this window has to start from that asymmetry and get its direction right.

Avia Solutions Limited. All rights reserved.
"""
import math

TOL = 0.20
LOG_LO = math.log(1.0 - TOL)      # -0.22314, the lower edge on log(f/A)
LOG_HI = math.log(1.0 + TOL)      # +0.18232, the upper edge
MID = (LOG_LO + LOG_HI) / 2.0     # -0.02041, the window centre


def within(ratio, tol=TOL):
    """The published band, on a forecast-over-actual ratio."""
    return abs(ratio - 1.0) <= tol


def within_log(e, shift=0.0):
    """The same band, on e = log(forecast/actual), with an optional shift applied to the forecast.

    A shift of s means the forecast was multiplied by exp(s), so the error becomes e + s.
    """
    return LOG_LO <= (e + shift) <= LOG_HI


def rate(ratios, tol=TOL):
    return 100.0 * sum(1 for x in ratios if within(x, tol)) / len(ratios) if ratios else 0.0


def rate_log(es, shift=0.0):
    return 100.0 * sum(1 for e in es if within_log(e, shift)) / len(es) if es else 0.0


def _selftest():
    assert within(1.20) and within(0.80), "the edges are inside the band"
    assert not within(1.2001) and not within(0.7999), "just outside is outside"
    for x in (0.80, 0.9, 1.0, 1.1, 1.20):
        assert within(x) == within_log(math.log(x)), "ratio and log forms must agree at %s" % x
    for x in (0.5, 0.79, 1.21, 3.0):
        assert within(x) == within_log(math.log(x)), "and must agree outside the band at %s" % x
    assert LOG_LO < 0 < LOG_HI, "the band straddles zero"
    assert abs(LOG_LO) > abs(LOG_HI), \
        "THE ASYMMETRY: the band is WIDER BELOW than above. Both 9 August failures inverted this."
    assert MID < 0, "so the window centre is below zero"
    assert abs(MID + 0.02041) < 1e-5, "window centre is -0.02041"
    print("  band on f/A            [%.4f, %.4f]" % (1 - TOL, 1 + TOL))
    print("  band on log(f/A)       [%+.5f, %+.5f]" % (LOG_LO, LOG_HI))
    print("  wider below by         %.5f" % (abs(LOG_LO) - abs(LOG_HI)))
    print("  window centre          %+.5f, so a median forecast sits ABOVE it" % MID)
    print("  derived multiplier     exp(%+.5f) = %.5f" % (MID, math.exp(MID)))
    print("  self-test passed")


if __name__ == "__main__":
    _selftest()
