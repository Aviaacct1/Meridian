#!/usr/bin/env python3
"""Size the schedule from demand instead of accepting the frequency it was given.

John, 7 August 2026: the generator took --freq uncritically, so a deck could be
built at a frequency the market does not support and then argue against its own
route. `schedule_viability` reports that after the fact. This decides it before.

WHY THIS HAS TO ITERATE. Frequency is not an input to demand and an output of it
separately: it is both. A nonstop's QSI share depends on schedule quality, and
schedule quality depends on frequency, so cutting the frequency cuts the share,
which cuts the demand, which cuts the frequency the demand supports. Solving it
in one pass gives a schedule the market will not fill. So the frequency is a
fixed point and it is found by running the engine round the loop until it stops
moving.

It converges downward and quickly, because each cut reduces demand by less than
it reduces capacity: three rounds is typical, five is the cap.

NOTHING HERE IS SILENT. Every round is recorded in `path`, oscillation and
non-convergence are named, and a failure returns the frequency it was given with
the reason attached. The caller prints it and the audit carries it.

The engine is passed in rather than imported, so this module has no dependency on
cortex_app and can be tested without a data store.

Avia Solutions Limited. All rights reserved.
"""

PLANNING_LF = 0.80      # the fill a sized schedule is written to
MIN_FREQ = 1
MAX_FREQ = 21           # three a day; beyond this the constraint is slots, not demand
MAX_ROUNDS = 5


def _load_of(fc):
    return ((fc or {}).get("capacity") or {}).get("load")


def _freq_of(fc):
    return ((fc or {}).get("capacity") or {}).get("freq")


def _closest(seen, target_lf):
    """The frequency whose planned load sits nearest the target.

    One rule, used everywhere a choice is made, so the sizer cannot be accused of
    deciding one way when it settles and another way when it does not. The
    tie-break is the HIGHER frequency: two schedules the same distance from the
    target are not equally good to propose, and the one with more flights carries
    more people and leaves more room in a soft season.
    """
    return min(seen, key=lambda f: (abs(seen[f][0] - target_lf), -f))


def size_schedule(forecast, freq_start=7, target_lf=PLANNING_LF,
                  min_freq=MIN_FREQ, max_freq=MAX_FREQ, max_rounds=MAX_ROUNDS):
    """Find the weekly frequency the demand actually supports.

    forecast    a callable taking one argument, the weekly frequency, and
                returning the engine's forecast dict. The caller supplies it, so
                every other input (aircraft, carrier type, season, overrides) is
                whatever the caller has already fixed.
    target_lf   the planned load factor the schedule is written to

    Returns:
      {"ok": bool, "reason": None | "engine" | "not sizable",
       "freq": int, "load": float, "fc": dict,
       "path": [(freq, load), ...], "rounds": int, "converged": bool,
       "note": str}

    `fc` is the forecast at the frequency returned, so the caller does not have to
    run the engine again. On failure `freq` is the frequency it started from and
    `note` says why, because a sizer that quietly hands back its input is the
    silent fallback this codebase keeps being bitten by.

    `reason` separates the two ways this can fail, and the caller should treat
    them differently. "engine" means the forecast itself broke and there is no
    deck to build. "not sizable" means the engine worked and the route simply
    cannot be sized by frequency: carry on at the frequency the user asked for,
    and say loudly why the sizing was not used.
    """
    freq = int(freq_start or 7)
    freq = max(min_freq, min(max_freq, freq))
    path, seen = [], {}
    fc = None

    for rounds in range(1, max_rounds + 1):
        try:
            fc = forecast(freq)
        except Exception as e:
            return {"ok": False, "reason": "engine", "freq": freq, "load": None, "fc": None,
                    "path": path, "rounds": rounds, "converged": False,
                    "note": "the engine failed at %s a week (%s: %s), so the "
                            "frequency was not sized"
                            % (freq, type(e).__name__, e)}
        if not isinstance(fc, dict) or not fc.get("ok", True):
            return {"ok": False, "reason": "engine", "freq": freq, "load": None, "fc": fc,
                    "path": path, "rounds": rounds, "converged": False,
                    "note": "the engine returned no forecast at %s a week (%s), "
                            "so the frequency was not sized"
                            % (freq, (fc or {}).get("error", "no error given"))}

        # INDUCED ROUTES CANNOT BE SIZED THIS WAY, and saying so is the whole
        # point of this check. On a route the engine classes as induced, demand
        # is FLOORED at capacity times an achieved seat factor for the type and
        # haul, because a new market does not pre-exist and the aircraft fills
        # from stimulation or network feed. Demand therefore follows capacity,
        # the load factor barely moves whatever the frequency, and the loop below
        # walks all the way to one flight a week and calls it converged. That is
        # not a schedule, it is the floor of the search. route_forecast.py says
        # the same thing from the other side: the protection against handing the
        # induced floor oversized capacity is the AUTO GAUGE, which sizes the
        # metal, not the frequency.
        if ((fc.get("demand") or {}).get("induced")):
            path.append((freq, round(float(_load_of(fc) or 0), 4)))
            return {"ok": False, "reason": "not sizable", "freq": freq,
                    "load": _load_of(fc), "fc": fc,
                    "path": path, "rounds": rounds, "converged": False,
                    "note": "the engine classes this as an INDUCED route, so "
                            "demand is floored at capacity times an achieved "
                            "seat factor and follows whatever capacity is "
                            "deployed. No frequency reaches a target fill, "
                            "because the load factor hardly moves. Size the "
                            "AIRCRAFT to the market instead, and read the "
                            "market as the constraint rather than the schedule."}

        load = _load_of(fc)
        if not load:
            return {"ok": False, "reason": "engine", "freq": freq, "load": None, "fc": fc,
                    "path": path, "rounds": rounds, "converged": False,
                    "note": "the engine returned no planned load factor at %s a "
                            "week, so there is nothing to size against" % freq}

        path.append((freq, round(float(load), 4)))

        # The same failure without the flag. If two materially different
        # frequencies return the same load factor, demand is tracking capacity
        # whatever the engine calls the route, and the loop has nothing to solve.
        for f0, (l0, _x) in seen.items():
            if abs(f0 - freq) >= 2 and abs(l0 - float(load)) < 0.02:
                return {"ok": False, "reason": "not sizable", "freq": freq,
                        "load": float(load), "fc": fc,
                        "path": path, "rounds": rounds, "converged": False,
                        "note": "demand is tracking capacity: %d a week and %d a "
                                "week both plan at %.0f%% load. Frequency cannot "
                                "reach a target fill on this route, so the "
                                "constraint is the market or the gauge, not the "
                                "schedule." % (f0, freq, float(load) * 100)}
        seen[freq] = (float(load), fc)

        # The frequency this load implies at the planning fill. Rounded half UP
        # explicitly: Python's round() is banker's rounding, so round(4.5) is 4,
        # and a sizer that rounds .5 to even is biased in a way nobody reading
        # the output would guess at.
        want = int(freq * float(load) / float(target_lf) + 0.5)
        want = max(min_freq, min(max_freq, want))

        if want == freq:
            # Settled. Before accepting it, try the frequency either side and
            # take whichever fills closest to the target. One flight a week is
            # the whole resolution of this answer, so the rounding rule would
            # otherwise decide the schedule, and no rounding rule should. Two
            # extra engine runs buys the argument away entirely.
            for nb in (freq - 1, freq + 1):
                if nb < min_freq or nb > max_freq or nb in seen:
                    continue
                try:
                    nfc = forecast(nb)
                except Exception:
                    continue
                nl = _load_of(nfc)
                if isinstance(nfc, dict) and nfc.get("ok", True) and nl:
                    seen[nb] = (float(nl), nfc)
                    path.append((nb, round(float(nl), 4)))
            best = _closest(seen, target_lf)
            bl, bfc = seen[best]
            extra = ("" if best == freq else
                     ", one either side tested and %d fills closer" % best)
            return {"ok": True, "reason": None, "freq": best, "load": bl, "fc": bfc,
                    "path": path, "rounds": rounds, "converged": True,
                    "note": "sized to %d a week at %.0f%% planned load, "
                            "converged in %d round%s%s"
                            % (best, bl * 100, rounds,
                               "" if rounds == 1 else "s", extra)}

        if want in seen:
            # Two frequencies each pointing at the other. Same rule as the settled
            # case below, deliberately: one decision, one rule. Nearest fill to
            # the target, and on a tie the higher frequency, because more flights
            # at the same distance from target is the safer schedule to propose.
            pick = _closest(seen, target_lf)
            pl, pfc = seen[pick]
            return {"ok": True, "reason": None, "freq": pick, "load": pl, "fc": pfc,
                    "path": path, "rounds": rounds, "converged": False,
                    "note": "the sizing oscillated between %s a week; took %d at "
                            "%.0f%% planned load, the fill nearest the %.0f%% "
                            "target"
                            % (" and ".join(str(f) for f in sorted(seen)), pick,
                               pl * 100, target_lf * 100)}
        freq = want

    pl, pfc = seen[freq] if freq in seen else (None, fc)
    return {"ok": True, "reason": None, "freq": freq, "load": pl, "fc": pfc, "path": path,
            "rounds": max_rounds, "converged": False,
            "note": "the sizing had not settled after %d rounds and stopped at "
                    "%d a week. Treat the frequency as indicative and set it by "
                    "hand." % (max_rounds, freq)}


def describe(result):
    """One line for the run report, plus the path so the reader can see the loop."""
    if not result:
        return "schedule sizing did not run"
    trail = " -> ".join("%dx at %.0f%%" % (f, l * 100) for f, l in result["path"])
    return "%s\n   path: %s" % (result["note"], trail or "no rounds completed")
