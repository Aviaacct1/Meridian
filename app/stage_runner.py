"""Resumable runner: does as many pending fits as fit in ~30s, checkpoints,
exits. Re-run until it prints ALL_DONE. State in /tmp/qsi_state.pkl."""
import time, pickle, os, sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

T0 = time.time()
BUDGET = 20
STATE = "/tmp/qsi_state.pkl"
PATH = "/sessions/happy-hopeful-brahmagupta/mnt/app/master_backtest_scored.csv"

NUM = ["gcd_km","natural","seats_market","capacity","base_fare",
       "dep_runway_m","dep_elev_m","arr_runway_m","arr_elev_m",
       "dep_n_airlines","dep_n_destinations","dep_total_freq",
       "dep_seats_on_offer","dep_lcc_freq_share","arr_n_airlines",
       "arr_n_destinations","arr_total_freq","arr_seats_on_offer",
       "arr_lcc_freq_share","dep_raw_transfer_pct","arr_raw_transfer_pct",
       "dep_premium_seat_share","dep_avg_gauge","arr_premium_seat_share",
       "arr_avg_gauge"]
CAT = ["haul_band","domestic","dep_country","arr_country","region",
       "type","carrier","hub_dest","service","seats_market_band"]
FEATS = NUM + CAT
LEAK = {"p2p_outturn","outturn_pax","fc_over_p2p","fc_over_out",
        "corrected_fc_over_out","forecast_pax","captured_uncapped",
        "feed_beyond","feed_behind","outturn_fare","dep_avg_fare_out",
        "arr_avg_fare_out","dep_avg_basefare_out","arr_avg_basefare_out",
        "propensity","propensity_basis","induced"}
assert not (set(FEATS) & LEAK)

df = pd.read_csv(PATH)
df = df[(df.fc_over_p2p.notna()) & (df.fc_over_p2p > 0)
        & (df.natural >= df.p2p_outturn) & (df.p2p_outturn > 0)
        & (df.capacity > 0)].reset_index(drop=True)
for c in CAT:
    df[c] = df[c].astype(str)
    vc = df[c].value_counts()
    df.loc[df[c].isin(vc[vc < 5].index), c] = "OTHER"
    df[c] = df[c].astype("category")

X = df[FEATS]
y = {"M1": np.log(df.fc_over_p2p.values),
     "M2a": np.log(np.clip(df.outturn_pax/df.capacity, 1e-3, None)),
     "M2b": np.log(np.clip(df.p2p_outturn/df.capacity, 1e-3, None))}
# M1y = M1 with year as numeric feature (trend test)
Xy = X.copy(); Xy["year"] = df.year.values.astype(float)

te_t = (df.year == 2018).values
folds = [("temporal", 0, ~te_t, te_t)]
gkf = GroupKFold(n_splits=5)
for k, (tr, te) in enumerate(gkf.split(X, y["M1"], groups=df.dep.values)):
    m_tr = np.zeros(len(df), bool); m_tr[tr] = True
    m_te = np.zeros(len(df), bool); m_te[te] = True
    folds.append(("grouped", k, m_tr, m_te))

JOBS = [(mod, fname, fk) for mod in ["M1","M2a","M2b","M1y"]
        for (fname, fk, _, _) in (folds if mod != "M1y" else folds[1:])]

state = pickle.load(open(STATE,"rb")) if os.path.exists(STATE) else {}

def make():
    return HistGradientBoostingRegressor(
        learning_rate=0.05, max_iter=2000, max_leaf_nodes=15,
        min_samples_leaf=40, l2_regularization=1.0, early_stopping=True,
        validation_fraction=0.15, n_iter_no_change=30,
        categorical_features=CAT, random_state=0)

done = 0
for mod, fname, fk in JOBS:
    key = (mod, fname, fk)
    if key in state:
        continue
    if time.time() - T0 > BUDGET:
        print(f"BUDGET_STOP after {done} new fits; "
              f"{sum(1 for j in JOBS if (j in state))+done}/{len(JOBS)} done")
        sys.exit(0)
    tr = te = None
    for (fn, k, m_tr, m_te) in folds:
        if fn == fname and k == fk:
            tr, te = m_tr, m_te
    tgt = y["M1"] if mod == "M1y" else y[mod]
    XX = Xy if mod == "M1y" else X
    m = make()
    m.fit(XX[tr], tgt[tr])
    state[key] = dict(pred_tr=m.predict(XX[tr]), pred_te=m.predict(XX[te]),
                      n_iter=int(m.n_iter_))
    pickle.dump(state, open(STATE, "wb"))
    done += 1
print(f"ALL_DONE {len(state)}/{len(JOBS)} fits complete")
