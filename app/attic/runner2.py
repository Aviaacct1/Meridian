"""Resumable runner, round 2. Substrates: C = master_complete.csv (2017-18,
new features), S = master_backtest_scored.csv (2016-18 + 2024, era work).
Re-run until ALL_DONE. State in /tmp/qsi2_state.pkl."""
import time, pickle, os, sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

T0 = time.time(); BUDGET = 20
STATE = "/tmp/qsi2_state.pkl"
APP = "/sessions/happy-hopeful-brahmagupta/mnt/app/"

CAT = ["haul_band","domestic","dep_country","arr_country","region",
       "type","carrier","hub_dest","service","seats_market_band"]
AIRPORT = ["dep_runway_m","dep_elev_m","arr_runway_m","arr_elev_m",
           "dep_n_airlines","dep_n_destinations","dep_total_freq",
           "dep_seats_on_offer","dep_lcc_freq_share","arr_n_airlines",
           "arr_n_destinations","arr_total_freq","arr_seats_on_offer",
           "arr_lcc_freq_share","dep_raw_transfer_pct","arr_raw_transfer_pct",
           "dep_premium_seat_share","dep_avg_gauge","arr_premium_seat_share",
           "arr_avg_gauge"]
CORE = ["gcd_km","natural","seats_market","capacity"]
NEWF = ["freq","gauge","block_min","dest_share","stimulation","coverage",
        "premium_share","att_exponent","planned_lf","capture_rate",
        "p2p_share","d_mkt_asif","d_growth_applied","d_share","d_dshare",
        "d_stim","d_coverage","d_captured","d_feed_fc","d_cap_bound",
        "dep_local_pax","dep_conn_pax","arr_local_pax","arr_conn_pax",
        "dep_non_mainline_share","arr_non_mainline_share"]
LEAK = {"p2p_outturn","outturn_pax","fc_over_p2p","fc_over_out",
        "corrected_fc_over_out","forecast_pax","captured_uncapped",
        "feed_beyond","feed_behind","outturn_fare","dep_avg_fare_out",
        "arr_avg_fare_out","dep_avg_basefare_out","arr_avg_basefare_out",
        "propensity","propensity_basis","induced","d_mkt_outturn"}

def load(path, fare_col):
    df = pd.read_csv(APP + path)
    df = df[(df.fc_over_p2p.notna()) & (df.fc_over_p2p > 0)
            & (df.natural >= df.p2p_outturn) & (df.p2p_outturn > 0)
            & (df.capacity > 0)].reset_index(drop=True)
    for c in CAT:
        df[c] = df[c].astype(str)
        vc = df[c].value_counts()
        df.loc[df[c].isin(vc[vc < 5].index), c] = "OTHER"
        df[c] = df[c].astype("category")
    return df

dC = load("master_complete.csv", "avg_fare")
dS = load("master_backtest_scored.csv", "base_fare")

OLD_C = CORE + ["avg_fare"] + AIRPORT + CAT      # avg_fare = pre-launch base fare
NEW_C = CORE + ["avg_fare"] + AIRPORT + NEWF + CAT
OLD_S = CORE + ["base_fare"] + AIRPORT + CAT
for fl in (OLD_C, NEW_C, OLD_S):
    assert not (set(fl) & LEAK)

def targets(df):
    return {"M1": np.log(df.fc_over_p2p.values),
            "M2a": np.log(np.clip(df.outturn_pax/df.capacity, 1e-3, None)),
            "M2b": np.log(np.clip(df.p2p_outturn/df.capacity, 1e-3, None))}
yC, yS = targets(dC), targets(dS)

def gfolds(df, n=5):
    out = []
    gkf = GroupKFold(n_splits=n)
    for k, (tr, te) in enumerate(gkf.split(df, groups=df.dep.values)):
        m_tr = np.zeros(len(df), bool); m_tr[tr] = True
        m_te = np.zeros(len(df), bool); m_te[te] = True
        out.append((k, m_tr, m_te))
    return out

pre_S = (dS.year < 2020).values
post_S = ~pre_S
foldsC = [("temporal", 0, (dC.year == 2017).values, (dC.year == 2018).values)] \
       + [("grouped", k, tr, te) for k, tr, te in gfolds(dC)]
foldsS = [("grouped", k, tr, te) for k, tr, te in gfolds(dS)] \
       + [("transfer", 0, pre_S, post_S)]
# era-internal grouped folds (masks are global-length, restricted to era)
for era, msk in [("pre", pre_S), ("post", post_S)]:
    sub = dS[msk]
    for k, tr, te in gfolds(sub):
        g_tr = np.zeros(len(dS), bool); g_tr[np.where(msk)[0][tr[:len(sub)]]] = True
        g_te = np.zeros(len(dS), bool); g_te[np.where(msk)[0][te[:len(sub)]]] = True
        foldsS.append((era, k, g_tr, g_te))

JOBS = []
for mod in ["M1", "M2a", "M2b"]:
    for fs in ["OLD", "NEW"]:
        for (fn, k, tr, te) in foldsC:
            JOBS.append(("C", mod, fs, fn, k))
    for (fn, k, tr, te) in foldsS:
        if fn == "grouped" or mod == "M2b":   # era folds: M2b only (+M1 transfer)
            JOBS.append(("S", mod, "OLD", fn, k))
JOBS.append(("S", "M1", "OLD", "transfer", 0))
JOBS = list(dict.fromkeys(JOBS))

state = pickle.load(open(STATE, "rb")) if os.path.exists(STATE) else {}

def make():
    return HistGradientBoostingRegressor(
        learning_rate=0.05, max_iter=2000, max_leaf_nodes=15,
        min_samples_leaf=40, l2_regularization=1.0, early_stopping=True,
        validation_fraction=0.15, n_iter_no_change=30,
        categorical_features=CAT, random_state=0)

done = 0
for job in JOBS:
    sub, mod, fs, fn, k = job
    if job in state:
        continue
    if time.time() - T0 > BUDGET:
        print(f"BUDGET_STOP {len(state)}/{len(JOBS)} done"); sys.exit(0)
    df, yy, folds = (dC, yC, foldsC) if sub == "C" else (dS, yS, foldsS)
    feats = {("C","OLD"): OLD_C, ("C","NEW"): NEW_C,
             ("S","OLD"): OLD_S}[(sub, fs)]
    tr = te = None
    for (f2, k2, m_tr, m_te) in folds:
        if f2 == fn and k2 == k:
            tr, te = m_tr, m_te
    m = make()
    m.fit(df[feats][tr], yy[mod][tr])
    state[job] = dict(pred_tr=m.predict(df[feats][tr]),
                      pred_te=m.predict(df[feats][te]), n_iter=int(m.n_iter_))
    pickle.dump(state, open(STATE, "wb"))
    done += 1
print(f"ALL_DONE {len(state)}/{len(JOBS)}")
