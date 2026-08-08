"""(1) OLD-feature M2b/M1 within-pre benchmark on v2 file (same rows as the
NEW-feature within-era CV). (2) Permutation importances within-pre, M1 + M2b.
State /tmp/qsi4c_state.pkl; rerun until ALL_DONE."""
import time, pickle, os, sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score

T0 = time.time(); BUDGET = 20
STATE = "/tmp/qsi4c_state.pkl"
PATH = ("/sessions/happy-hopeful-brahmagupta/mnt/app/"
        "master_v3_complete_dot.csv")

CAT = ["haul_band","domestic","dep_country","arr_country","region",
       "type","carrier","hub_dest","service","seats_market_band"]
OLDNUM = ["gcd_km","natural","seats_market","capacity","avg_fare",
          "dep_runway_m","dep_elev_m","arr_runway_m","arr_elev_m",
          "dep_n_airlines","dep_n_destinations","dep_total_freq",
          "dep_seats_on_offer","dep_lcc_freq_share","arr_n_airlines",
          "arr_n_destinations","arr_total_freq","arr_seats_on_offer",
          "arr_lcc_freq_share","dep_raw_transfer_pct","arr_raw_transfer_pct",
          "dep_premium_seat_share","dep_avg_gauge","arr_premium_seat_share",
          "arr_avg_gauge"]
NEWNUM = OLDNUM + ["freq","gauge","block_min","dest_share","stimulation",
       "coverage","premium_share","att_exponent","planned_lf","capture_rate",
       "p2p_share","d_mkt_asif","d_growth_applied","d_share","d_dshare",
       "d_stim","d_coverage","d_captured","d_feed_fc","d_cap_bound",
       "dep_non_mainline_share","arr_non_mainline_share",
       "db1b_market_v","db1b_fare_v","db1b_to_sabre","carrier_casm_c",
       "carrier_rasm_c","carrier_stage_km","is_regional"]

df = pd.read_csv(PATH)
df = df[(df.fc_over_p2p.notna()) & (df.fc_over_p2p > 0)
        & (df.natural >= df.p2p_outturn) & (df.p2p_outturn > 0)
        & (df.capacity > 0)].reset_index(drop=True)
for c in CAT:
    df[c] = df[c].astype(str)
    vc = df[c].value_counts()
    df.loc[df[c].isin(vc[vc < 5].index), c] = "OTHER"
    df[c] = df[c].astype("category")
sub = df[(df.year < 2020)].reset_index(drop=True)

w20 = lambda r: float(np.mean((r >= 0.8) & (r <= 1.2)))
slog = lambda r: float(np.std(np.log(np.clip(r, 1e-9, None))))
state = pickle.load(open(STATE, "rb")) if os.path.exists(STATE) else {}

def make():
    return HistGradientBoostingRegressor(
        learning_rate=0.05, max_iter=2000, max_leaf_nodes=15,
        min_samples_leaf=40, l2_regularization=1.0, early_stopping=True,
        validation_fraction=0.15, n_iter_no_change=30,
        categorical_features=CAT, random_state=0)

ys = {"M1": np.log(sub.fc_over_p2p.values),
      "M2b": np.log(np.clip(sub.p2p_outturn/sub.capacity, 1e-3, None))}
gkf = GroupKFold(n_splits=5)
folds = list(gkf.split(sub, groups=sub.dep.values))

# OLD-feature within-pre CV
for mod in ["M1", "M2b"]:
    for k, (tr, te) in enumerate(folds):
        key = ("OLD", mod, k)
        if key in state: continue
        if time.time() - T0 > BUDGET:
            print(f"BUDGET_STOP {len(state)}"); sys.exit(0)
        m = make()
        m.fit(sub[OLDNUM + CAT].iloc[tr], ys[mod][tr])
        state[key] = dict(pred_te=m.predict(sub[OLDNUM + CAT].iloc[te]), te=te)
        pickle.dump(state, open(STATE, "wb"))

for mod in ["M1", "M2b"]:
    rats = []
    for k, (tr, te) in enumerate(folds):
        s = state[("OLD", mod, k)]
        if mod == "M1":
            rats.append(sub.fc_over_p2p.values[s["te"]] / np.exp(s["pred_te"]))
        else:
            rats.append(sub.capacity.values[s["te"]] * np.exp(s["pred_te"])
                        / sub.p2p_outturn.values[s["te"]])
    r = np.concatenate(rats)
    print(f"OLD-features within-pre {mod:3s}: held-out w20 {w20(r):.3f} | "
          f"sigma {slog(r):.3f}")

# importances within-pre: train on folds[0] train, test folds[0] test
FEATS = NEWNUM + CAT
for mod in ["M1", "M2b"]:
    key = ("IMP", mod)
    if key in state: continue
    if time.time() - T0 > BUDGET:
        print(f"BUDGET_STOP {len(state)}"); sys.exit(0)
    tr, te = folds[0]
    m = make(); m.fit(sub[FEATS].iloc[tr], ys[mod][tr])
    Xte = sub[FEATS].iloc[te].reset_index(drop=True); yte = ys[mod][te]
    b = r2_score(yte, m.predict(Xte))
    rng = np.random.RandomState(0); res = []
    for f in FEATS:
        Xp = Xte.copy(); Xp[f] = Xp[f].values[rng.permutation(len(Xp))]
        res.append((b - r2_score(yte, m.predict(Xp)), f))
    res.sort(reverse=True)
    state[key] = dict(r2=b, top=res[:15])
    pickle.dump(state, open(STATE, "wb"))
for mod in ["M1", "M2b"]:
    s = state[("IMP", mod)]
    print(f"\n{mod} within-pre held-out r2 {s['r2']:.3f}; top 15:")
    for d, f in s["top"]:
        print(f"  {f:26s} {d:+.4f}")
print("ALL_DONE")
