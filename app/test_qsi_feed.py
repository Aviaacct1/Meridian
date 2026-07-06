#!/usr/bin/env python3
"""
Avia Cortex - Engine V2 unit tests: qsi_feed on synthetic boards (no databases).
Checks the properties the QSI feed MUST have and the parked mct_bank haircut lacked:
schedule quality discriminates, alliance ranks, and departure time moves the share the
right way. Run:  py -3.12 test_qsi_feed.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import qsi_feed as QF


class FakeBoards:
    """dep/arr boards from a dict: {("dep"|"arr", week, airport): [leg dicts]}."""
    def __init__(self, data):
        self.data = data

    def dep_rows(self, week, airport):
        return self.data.get(("dep", week, airport), [])

    def arr_rows(self, week, airport):
        return self.data.get(("arr", week, airport), [])


def leg(dep, arr, carrier, dep_mins, arr_mins, flying, freq=7, alliance="",
        dep_country="XX", arr_country="YY"):
    return {"dep": dep, "arr": arr, "carrier": carrier, "alliance": alliance,
            "dep_mins": dep_mins, "arr_mins": arr_mins, "flying": flying, "freq": freq,
            "dep_country": dep_country, "arr_country": arr_country}


MCT = {}          # empty master -> mct_bank default 60 everywhere
W = "2025-01-06"
PASSED = FAILED = 0


def check(name, cond, note=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  ok    {name}")
    else:
        FAILED += 1
        print(f"  FAIL  {name}  {note}")


def beyond(boards, dep_mins, markets=("MMM",), airline="NR", flying=600, freq=7, cfg=None):
    return QF.beyond_capture(boards, W, ["ORG"], "HUB", list(markets), airline,
                             dep_mins, flying, freq, mct=MCT, cfg=cfg)


# ---------------------------------------------------------------- 1. legality
print("1. illegal connections score zero")
# onward departs HUB 10:00; new route arrives 09:30 -> 30 min < MCT 60 -> illegal
b = FakeBoards({("dep", W, "HUB"): [leg("HUB", "MMM", "ZZ", 600, 900, 180)],
                ("dep", W, "ORG"): []})
s = beyond(b, dep_mins=0, flying=570)     # dep 00:00 + 570 = arrive 09:30
check("buffer below MCT -> share 0", s["MMM"] == 0.0, f"got {s['MMM']}")
s = beyond(b, dep_mins=0, flying=530)     # arrive 08:50 -> buffer 70 -> legal
check("buffer above MCT -> share > 0", s["MMM"] > 0.0, f"got {s['MMM']}")

# ------------------------------------------------- 2. tight legal beats long layover
print("2. elapsed-time decay: tight legal connection beats a long layover")
# competitor over RIV with a 6-hour layover; new route with a 90-minute one
b = FakeBoards({
    ("dep", W, "HUB"): [leg("HUB", "MMM", "ZZ", 690, 990, 180)],     # dep 11:30
    ("dep", W, "ORG"): [leg("ORG", "RIV", "CC", 0, 240, 240)],       # arrives RIV 04:00
    ("dep", W, "RIV"): [leg("RIV", "MMM", "CC", 600, 900, 180)],     # dep 10:00: 6 h layover
})
s_tight = beyond(b, dep_mins=0, flying=600)   # arrive HUB 10:00, 90 min connect
b2 = FakeBoards({
    ("dep", W, "HUB"): [leg("HUB", "MMM", "ZZ", 690, 990, 180)],
    ("dep", W, "ORG"): [leg("ORG", "RIV", "CC", 0, 240, 240)],
    ("dep", W, "RIV"): [leg("RIV", "MMM", "CC", 330, 630, 180)],     # dep 05:30: 90 min layover
})
s_loose = beyond(b2, dep_mins=0, flying=600)
check("share higher when the COMPETITOR's connection is worse",
      s_tight["MMM"] > s_loose["MMM"], f"{s_tight['MMM']:.3f} vs {s_loose['MMM']:.3f}")

# ------------------------------------------------------------- 3. alliance ranking
print("3. connection type: online > alliance > interline for the new route")
# identical competition over RIV in every case; only the new route's onward cnx type varies
def with_onward(car, alli):
    return FakeBoards({
        ("dep", W, "HUB"): [leg("HUB", "MMM", car, 720, 1020, 180, alliance=alli)],
        ("dep", W, "ORG"): [leg("ORG", "RIV", "CC", 0, 240, 240)],
        ("dep", W, "RIV"): [leg("RIV", "MMM", "CC", 330, 630, 180)],
    })
s_online = QF.beyond_capture(with_onward("BA", "OW"), W, ["ORG"], "HUB", ["MMM"], "BA",
                             0, 600, 7, mct=MCT)     # BA onto BA: online
sa = QF.beyond_capture(with_onward("BA", "OW"), W, ["ORG"], "HUB", ["MMM"], "AA",
                       0, 600, 7, mct=MCT)           # AA onto BA: oneworld alliance
si = QF.beyond_capture(with_onward("BA", "OW"), W, ["ORG"], "HUB", ["MMM"], "NR",
                       0, 600, 7, mct=MCT)           # NR onto BA: interline
check("online beats alliance", s_online["MMM"] > sa["MMM"],
      f"{s_online['MMM']:.3f} vs {sa['MMM']:.3f}")
check("alliance beats interline", sa["MMM"] > si["MMM"],
      f"{sa['MMM']:.3f} vs {si['MMM']:.3f}")

# ------------------------------------------------------- 4. departure time moves share
print("4. departure time is a real input: pre-wave arrival beats post-wave")
wave = [leg("HUB", "MMM", "ZZ", 780, 1080, 180),      # bank of onward departures 13:00-14:00
        leg("HUB", "MMM", "ZZ", 810, 1110, 180),
        leg("HUB", "MMM", "ZZ", 840, 1140, 180)]
comp = {("dep", W, "ORG"): [leg("ORG", "RIV", "CC", 0, 300, 300)],
        ("dep", W, "RIV"): [leg("RIV", "MMM", "CC", 420, 720, 180)]}
b = FakeBoards({("dep", W, "HUB"): wave, **comp})
s_pre = beyond(b, dep_mins=60, flying=600)     # arrive 11:00, 120-180 min buffers
s_post = beyond(b, dep_mins=300, flying=600)   # arrive 15:00, missed the whole wave
check("arrival ahead of the wave scores", s_pre["MMM"] > 0, f"got {s_pre['MMM']}")
check("arrival behind the wave loses the market", s_post["MMM"] == 0.0,
      f"got {s_post['MMM']}")

print("5. the optimiser finds the wave")
best_dep, shares = QF.optimise_dep(b, W, ["ORG"], "HUB", ["MMM"], {"MMM": 1000.0},
                                   "NR", 600, 7, step=60, mct=MCT)
arr = (best_dep + 600) % 1440
check("optimised arrival lands 60-720 min before the last bank departure",
      any(QF._gap(arr, l["dep_mins"]) >= 60 for l in wave)
      and shares["MMM"] >= s_pre["MMM"] - 1e-9,
      f"best_dep {best_dep} (arr {arr}), share {shares['MMM']:.3f}")

# ------------------------------------------------------------ 6. frequency cap
print("6. frequency cap: a 21x/wk codeshare pile-up cannot drown the entrant")
heavy = FakeBoards({
    ("dep", W, "HUB"): [leg("HUB", "MMM", "ZZ", 720, 1020, 180)],
    ("dep", W, "ORG"): [leg("ORG", "RIV", "CC", 0, 240, 240, freq=21),
                        leg("ORG", "RIV", "CC", 30, 270, 240, freq=21)],
    ("dep", W, "RIV"): [leg("RIV", "MMM", "CC", 360, 660, 180, freq=21),
                        leg("RIV", "MMM", "CC", 400, 700, 180, freq=21)],
})
s_capped = beyond(heavy, dep_mins=0, flying=600)
s_uncapped = beyond(heavy, dep_mins=0, flying=600, cfg={"freq_cap": 999.0})
check("cap lifts the entrant's share vs uncapped", s_capped["MMM"] > s_uncapped["MMM"],
      f"{s_capped['MMM']:.3f} vs {s_uncapped['MMM']:.3f}")

# ------------------------------------------------------------- 7. behind mirror
print("7. behind side mirrors: feeder arrival must beat the origin MCT")
bb = FakeBoards({
    ("arr", W, "ORG"): [leg("YYY", "ORG", "NR", 480, 540, 60)],   # feeder arrives 09:00
    ("dep", W, "YYY"): [],
})
sh = QF.behind_capture(bb, W, ["ORG"], ["DDD"], ["YYY"], "NR", 630, mct=MCT,
                       cfg={"route_flying_mins": 600, "route_freq": 7})
check("legal behind connection scores", sh["YYY"] > 0, f"got {sh['YYY']}")
sh2 = QF.behind_capture(bb, W, ["ORG"], ["DDD"], ["YYY"], "NR", 570, mct=MCT,
                        cfg={"route_flying_mins": 600, "route_freq": 7})
check("dep 30 min after feeder arrival is illegal -> 0", sh2["YYY"] == 0.0,
      f"got {sh2['YYY']}")

# ---------------------------------------------------------------- 8. share bounds
print("8. shares are proper shares")
vals = [s_tight["MMM"], s_loose["MMM"], s_pre["MMM"], s_capped["MMM"], sa["MMM"]]
check("all shares within (0, 1]", all(0 < v <= 1.0 for v in vals), f"{vals}")

print(f"\n{PASSED} passed, {FAILED} failed")
sys.exit(1 if FAILED else 0)
