#!/usr/bin/env python3
"""Does the entered schedule stand up commercially. Advisory, never blocking.

John, 7 August 2026: a deck that prints a 38% planned load factor argues against
its own route. No airline flies a long-haul narrowbody at that fill, and a
network planner reading it concludes the service fails as proposed. The forecast
is not the problem, the fixed frequency is.

The check lives here, beside the engine, rather than in the deck generator,
because the dashboard needs it as much as the deck does and there must be one
implementation of it. `forecast_spec.schedule_viability` in the deck generator
delegates to this function.

It advises. It never blocks and never changes a number: a client is entitled to
print the schedule they asked for, and this says so before they do, and says
what the demand would actually support.

Avia Solutions Limited. All rights reserved.
"""

VIABLE_LF = 0.65        # below this, a long-haul schedule is not a proposition
MARGINAL_LF = 0.75      # below this, it is thin and worth a second look
PLANNING_LF = 0.80      # the fill a sized schedule is written to
OPTIMISER_LF = 0.55     # cortex_app MIN_OPT_LF: keep the two the same on purpose


def _pct(x, dp=0):
    try:
        return ("%%.%df%%%%" % dp) % (float(x) * 100.0)
    except (TypeError, ValueError):
        return ""


def _money(x):
    try:
        return "{:,.0f}".format(float(x))
    except (TypeError, ValueError):
        return "an unstated amount"


def schedule_viability(fc, min_lf=VIABLE_LF, target=PLANNING_LF, sized=False):
    """Returns None where the schedule stands up, otherwise the advisory.

    {"band": "NOT A PROPOSITION" | "THIN", "load_factor": float,
     "frequency": int, "sized_frequency": int | None, "message": str,
     "question": str}

    `question` is the dashboard's wording: it asks, it does not instruct.
    """
    cap = (fc or {}).get("capacity") or {}
    lf = cap.get("load")
    freq = cap.get("freq")
    if not lf or lf >= MARGINAL_LF:
        return None

    # THE OPTIMISER OUTRANKS THIS CHECK, and it has to, because otherwise two
    # house rules contradict each other in front of a client. This function is a
    # heuristic with a 65% floor. /api/optimise is a profit-maximising sweep over
    # the airline, the gauge, the frequency and the season, and it carries its
    # own floor at 55%. On EDI to AUS it chose a summer 3x that makes 717,078 a
    # year at 57%, and this check then called the same schedule "not a
    # proposition". Both cannot be Avia's view. A seasonal service runs a lower
    # average load by design, which is part of why the optimiser picked summer.
    # So where the optimiser chose the schedule AND the schedule makes money, the
    # finding is reported rather than objected to.
    opt = (fc or {}).get("optimised") or {}
    profit = opt.get("annual_profit")
    if opt and profit and profit > 0:
        if lf >= OPTIMISER_LF:
            return {"band": "OPTIMISER'S CHOICE", "load_factor": lf,
                    "frequency": freq, "sized_frequency": None, "was_sized": True,
                    "message": "The optimiser chose this schedule: %s%s a week%s, "
                               "planning at %s load and returning %s a year. It "
                               "swept the airline, the gauge, the frequency and "
                               "the season and this was the most profitable. A "
                               "fill below the usual planning target is a "
                               "deliberate part of that answer, not an oversight."
                               % ((opt.get("airline") + ", ") if opt.get("airline") else "",
                                  opt.get("freq") or freq,
                                  (" over the %s season" % opt["season"])
                                  if opt.get("season") and opt["season"] != "annual" else "",
                                  _pct(lf), _money(profit)),
                    "question": ""}
        # below even the optimiser's own floor, so it is worth saying out loud
        return {"band": "THIN, OPTIMISED", "load_factor": lf, "frequency": freq,
                "sized_frequency": None, "was_sized": True,
                "message": "The optimiser chose this schedule and it returns %s a "
                           "year, but at %s the fill is below the optimiser's own "
                           "%s floor. Check the season and the gauge before this "
                           "goes to an airline."
                           % (_money(profit), _pct(lf), _pct(OPTIMISER_LF)),
                "question": ""}
    band = "NOT A PROPOSITION" if lf < min_lf else "THIN"
    # "as entered" is wrong once the schedule has been sized, and the distinction
    # matters: a thin fill on a frequency the user chose is an input to change,
    # while a thin fill on a sized schedule means the market is the constraint
    # and no frequency fixes it.
    msg = ["The schedule %s plans at %s load factor."
           % ("as sized" if sized else "as entered", _pct(lf))]
    if band == "NOT A PROPOSITION":
        msg.append("No airline will take a long-haul route to its board at that "
                   "fill, so the deck would argue against its own case.")
    else:
        msg.append("That is thin for a long-haul service and leaves little room "
                   "for a soft season.")
    sized_freq = None
    induced = bool(((fc or {}).get("demand") or {}).get("induced"))
    if induced:
        # The same trap the frequency sizer had to be taught about. On an induced
        # route demand is floored at deployed capacity, so "the same demand fills
        # three a week at 80%" is arithmetic on a number that would not survive
        # the cut: reduce the capacity and the floored demand reduces with it,
        # and the fill lands back where it started. Offering that advice here
        # would send the reader to a schedule that does not exist.
        msg.append("This route is modelled as an induced market, so demand is "
                   "floored at the capacity deployed and follows it down. "
                   "Cutting the frequency will not raise the fill. The gauge and "
                   "the market are the constraint, not the schedule.")
    elif sized:
        msg.append("The frequency was already sized to the demand, so this is "
                   "the market talking and not the schedule. The route does not "
                   "fill at any frequency on this aircraft.")
    elif freq and lf:
        # the frequency that carries the same demand at a normal planning load
        sized_freq = max(1, int(round(float(freq) * float(lf) / target)))
        if sized_freq < freq:
            msg.append("The same demand fills %s a week at circa %.0f%% load on "
                       "the same aircraft. Consider opening at that frequency "
                       "and building up as the route matures."
                       % (("%d flights" % sized_freq) if sized_freq > 1 else "1 flight",
                          target * 100))
        else:
            sized_freq = None
    question = ("At %s load factor this is unlikely to be a route an airline "
                "will consider. Do you want to proceed?" % _pct(lf))
    return {"band": band, "load_factor": lf, "frequency": freq,
            "sized_frequency": sized_freq, "was_sized": bool(sized),
            "message": " ".join(msg), "question": question}
