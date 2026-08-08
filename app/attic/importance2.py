"""Manual permutation importance, one model per invocation: argv[1] = M1|M2b."""
import sys, time
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score

NAME = sys.argv[1]
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
yv = (np.log(df.fc_over_p2p.values) if NAME == "M1"
      else np.log(np.clip(df.p2p_outturn/df.capacity, 1e-3, None)))
te = (df.year == 2018).values
tr = ~te

m = HistGradientBoostingRegressor(
    learning_rate=0.05, max_iter=2000, max_leaf_nodes=15,
    min_samples_leaf=40, l2_regularization=1.0, early_stopping=True,
    validation_fraction=0.15, n_iter_no_change=30,
    categorical_features=CAT, random_state=0)
m.fit(X[tr], yv[tr])
Xte = X[te].reset_index(drop=True)
yte = yv[te]
base_r2 = r2_score(yte, m.predict(Xte))
rng = np.random.RandomState(0)
res = []
for f in FEATS:
    drops = []
    for rep in range(2):
        Xp = Xte.copy()
        Xp[f] = Xp[f].values[rng.permutation(len(Xp))]
        drops.append(base_r2 - r2_score(yte, m.predict(Xp)))
    res.append((float(np.mean(drops)), f))
res.sort(reverse=True)
print(f"{NAME} held-out r2 {base_r2:.3f}; top 15 permutation importances:")
for d, f in res[:15]:
    print(f"  {f:26s} {d:+.4f}")
