"""Within-era grouped CV on master_v2_complete_dot.csv (era-consistent
capacity basis). M1 + M2b, pre (2016-18) and post (2024).
State /tmp/qsi3b_state.pkl; rerun until ALL_DONE."""
import time, pickle, os, sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

T0 = time.time(); BUDGET = 20
STATE = "/tmp/qsi3b_state.pkl"
PATH = ("/sessions/happy-hopeful-brahmagupta/mnt/app/"
        "master_v2_complete_dot.csv")

CAT = ["haul_band","domestic","dep_country","arr_country","region",
       "type","carrier","hub_dest","service","seats_market_band"]
NUM = ["gcd_km","natural","seats_market","capacity","freq","gauge",
       "block_min","dest_share","stimulation","coverage","premium_share",
       "att_exponent","planned_lf","capture_rate","avg_fare","p2p_share",
       "d_mkt_asif","d_growth_applied","d_share","d_dshare","d_stim",
       "d_coverage","d_captured","d_feed_fc","d_cap_bound",
       "dep_runway_m","dep_elev_m","arr_runway_m","arr_elev_m",
       "dep_n_airlines","dep_n_destinations","dep_total_freq",
       "dep_seats_on_offer","dep_lcc_freq_share","arr_n_airlines",
       "arr_n_destinations","arr_total_freq","arr_seats_on_offer",
       "arr_lcc_freq_share","dep_raw_transfer_pct","arr_raw_transfer_pct",
       "dep_premium_seat_share","dep_avg_gauge","dep_non_mainline_share",
       "arr_premium_seat_share","arr_avg_gauge","arr_non_mainline_share",
       "db1b_market_v","db1b_fare_v","db1b_to_sabre","carrier_casm_c",
       "carrier_rasm_c","carrier_stage_km","is_regional"]
FEATS = NUM + CAT

df = pd.read_csv(PATH)
df = df[(df.fc_over_p2p.notna()) & (df.fc_over_p2p > 0)
        & (df.natural >= df.p2p_outturn) & (df.p2p_outturn > 0)
        & (df.capacity > 0)].reset_index(drop=True)
for c in CAT:
    df[c] = df[c].astype(str)
    vc = df[c].value_counts()
    df.loc[df[c].isin(vc[vc < 5].index), c] = "OTHER"
    df[c] = df[c].astype("category")

w20 = lambda r: float(np.mean((r >= 0.8) & (r <= 1.2)))
slog = lambda r: float(np.std(np.log(np.clip(r, 1e-9, None))))
state = pickle.load(open(STATE, "rb")) if os.path.exists(STATE) else {}

def make():
    return HistGradientBoostingRegressor(
        learning_rate=0.05, max_iter=2000, max_leaf_nodes=15,
        min_samples_leaf=40, l2_regularization=1.0, early_stopping=True,
        validation_fraction=0.15, n_iter_no_change=30,
        categorical_features=CAT, random_state=0)

for era, emsk in [("pre", (df.year < 2020).values),
                  ("post", (df.year == 2024).values)]:
    sub = df[emsk].reset_index(drop=True)
    X = sub[FEATS]
    ys = {"M1": np.log(sub.fc_over_p2p.values),
          "M2b": np.log(np.clip(sub.p2p_outturn/sub.capacity, 1e-3, None))}
    n_splits = 5
    gkf = GroupKFold(n_splits=n_splits)
    folds = list(gkf.split(X, ys["M1"], groups=sub.dep.values))
    for mod in ["M1", "M2b"]:
        for k, (tr, te) in enumerate(folds):
            key = (era, mod, k)
            if key in state:
                continue
            if time.time() - T0 > BUDGET:
                print(f"BUDGET_STOP {len(state)}/20"); sys.exit(0)
            m = make()
            m.fit(X.iloc[tr], ys[mod][tr])
            state[key] = dict(pred_te=m.predict(X.iloc[te]), te=te,
                              pred_tr_w20=None)
            pickle.dump(state, open(STATE, "wb"))

# score
for era, emsk in [("pre", (df.year < 2020).values),
                  ("post", (df.year == 2024).values)]:
    sub = df[emsk].reset_index(drop=True)
    base = sub.fc_over_p2p.values
    for mod in ["M1", "M2b"]:
        rats = []
        for k in range(5):
            if (era, mod, k) not in state:
                break
            s = state[(era, mod, k)]
            te = s["te"]
            if mod == "M1":
                rats.append(base[te] / np.exp(s["pred_te"]))
            else:
                rats.append(sub.capacity.values[te] * np.exp(s["pred_te"])
                            / sub.p2p_outturn.values[te])
        else:
            r = np.concatenate(rats)
            print(f"{era:4s} {mod:3s} grouped-CV held-out w20 {w20(r):.3f} | "
                  f"sigma {slog(r):.3f} | n {len(r)} | baseline {w20(base):.3f}")
print("ALL_DONE" if len(state) >= 20 else f"PARTIAL {len(state)}/20")
