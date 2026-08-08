"""Permutation importance on complete substrate, NEW feature set.
argv[1] = M1 | M2b."""
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score

NAME = sys.argv[1]
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
NEWF = ["freq","gauge","block_min","dest_share","stimulation","coverage",
        "premium_share","att_exponent","planned_lf","capture_rate",
        "p2p_share","d_mkt_asif","d_growth_applied","d_share","d_dshare",
        "d_stim","d_coverage","d_captured","d_feed_fc","d_cap_bound",
        "dep_local_pax","dep_conn_pax","arr_local_pax","arr_conn_pax",
        "dep_non_mainline_share","arr_non_mainline_share"]
FEATS = ["gcd_km","natural","seats_market","capacity","avg_fare"] \
        + AIRPORT + NEWF + CAT

df = pd.read_csv(APP + "master_complete.csv")
df = df[(df.fc_over_p2p.notna()) & (df.fc_over_p2p > 0)
        & (df.natural >= df.p2p_outturn) & (df.p2p_outturn > 0)
        & (df.capacity > 0)].reset_index(drop=True)
for c in CAT:
    df[c] = df[c].astype(str)
    vc = df[c].value_counts()
    df.loc[df[c].isin(vc[vc < 5].index), c] = "OTHER"
    df[c] = df[c].astype("category")

X = df[FEATS]
yv = (np.log(df.fc_over_p2p.values) if NAME == "M1"
      else np.log(np.clip(df.p2p_outturn/df.capacity, 1e-3, None)))
te = (df.year == 2018).values; tr = ~te
m = HistGradientBoostingRegressor(
    learning_rate=0.05, max_iter=2000, max_leaf_nodes=15,
    min_samples_leaf=40, l2_regularization=1.0, early_stopping=True,
    validation_fraction=0.15, n_iter_no_change=30,
    categorical_features=CAT, random_state=0)
m.fit(X[tr], yv[tr])
Xte = X[te].reset_index(drop=True); yte = yv[te]
base_r2 = r2_score(yte, m.predict(Xte))
rng = np.random.RandomState(0)
res = []
for f in FEATS:
    drops = []
    for rep in range(3):
        Xp = Xte.copy()
        Xp[f] = Xp[f].values[rng.permutation(len(Xp))]
        drops.append(base_r2 - r2_score(yte, m.predict(Xp)))
    res.append((float(np.mean(drops)), f))
res.sort(reverse=True)
print(f"{NAME} NEW-features held-out r2 {base_r2:.3f}; top 18:")
for d, f in res[:18]:
    print(f"  {f:26s} {d:+.4f}")
