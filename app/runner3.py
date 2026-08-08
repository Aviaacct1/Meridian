"""Resumable runner, round 3: master_v2_complete_dot.csv, full feature set
incl. DOT columns. Re-run until ALL_DONE. State /tmp/qsi3_state.pkl."""
import time, pickle, os, sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

T0 = time.time(); BUDGET = 20
STATE = "/tmp/qsi3_state.pkl"
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
LEAK = {"p2p_outturn","outturn_pax","fc_over_p2p","fc_over_out",
        "corrected_fc_over_out","forecast_pax","captured_uncapped",
        "feed_beyond","feed_behind","d_mkt_outturn","dep_avg_fare_out",
        "arr_avg_fare_out","dep_avg_basefare_out","arr_avg_basefare_out",
        "propensity","propensity_basis","induced","outturn_fare"}
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

te_t = (df.year == 2024).values
folds = [("temporal", 0, ~te_t, te_t)]
gkf = GroupKFold(n_splits=5)
for k, (tr, te) in enumerate(gkf.split(X, y["M1"], groups=df.dep.values)):
    m_tr = np.zeros(len(df), bool); m_tr[tr] = True
    m_te = np.zeros(len(df), bool); m_te[te] = True
    folds.append(("grouped", k, m_tr, m_te))

JOBS = [(mod, fn, k) for mod in ["M1","M2a","M2b"]
        for (fn, k, _, _) in folds]
state = pickle.load(open(STATE, "rb")) if os.path.exists(STATE) else {}

def make():
    return HistGradientBoostingRegressor(
        learning_rate=0.05, max_iter=2000, max_leaf_nodes=15,
        min_samples_leaf=40, l2_regularization=1.0, early_stopping=True,
        validation_fraction=0.15, n_iter_no_change=30,
        categorical_features=CAT, random_state=0)

for job in JOBS:
    mod, fn, k = job
    if job in state:
        continue
    if time.time() - T0 > BUDGET:
        print(f"BUDGET_STOP {len(state)}/{len(JOBS)}"); sys.exit(0)
    tr = te = None
    for (f2, k2, m_tr, m_te) in folds:
        if f2 == fn and k2 == k:
            tr, te = m_tr, m_te
    m = make()
    m.fit(X[tr], y[mod][tr])
    state[job] = dict(pred_tr=m.predict(X[tr]), pred_te=m.predict(X[te]),
                      n_iter=int(m.n_iter_))
    pickle.dump(state, open(STATE, "wb"))
print(f"ALL_DONE {len(state)}/{len(JOBS)}")
