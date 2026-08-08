"""Distil the M1 correction model into named multi-variable subgroups,
then check each subgroup's correction for drift across years."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor, _tree

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
y1 = np.log(df.fc_over_p2p.values)
base = df.fc_over_p2p.values
m = HistGradientBoostingRegressor(
    learning_rate=0.05, max_iter=2000, max_leaf_nodes=15,
    min_samples_leaf=40, l2_regularization=1.0, early_stopping=True,
    validation_fraction=0.15, n_iter_no_change=30,
    categorical_features=CAT, random_state=0)
m.fit(X, y1)
pred = m.predict(X)

Xd = pd.get_dummies(X, columns=CAT)
dt = DecisionTreeRegressor(max_depth=4, min_samples_leaf=80, random_state=0)
dt.fit(Xd, pred)
tree = dt.tree_
fnames = Xd.columns.to_numpy()

def rules(node=0, conds=(), out=None):
    out = out if out is not None else []
    if tree.children_left[node] == _tree.TREE_LEAF:
        out.append((conds, node)); return out
    f, t = fnames[tree.feature[node]], tree.threshold[node]
    if f in NUM:
        lo, hi = f"{f}<={t:,.0f}", f"{f}>{t:,.0f}"
    else:
        lo, hi = f"NOT {f}", f"{f}"
    rules(tree.children_left[node], conds + (lo,), out)
    rules(tree.children_right[node], conds + (hi,), out)
    return out

leaf = dt.apply(Xd)
w20 = lambda r: float(np.mean((r >= 0.8) & (r <= 1.2)))
yr = df.year.values
print("SUBGROUP TABLE (leaves of tree distilled from full-feature model)")
stats = []
for conds, node in rules():
    msk = leaf == node
    n = int(msk.sum())
    med = float(np.median(base[msk]))
    stats.append((n, med, w20(base[msk]/med), " & ".join(conds), msk))
for n, med, cw, rule, msk in sorted(stats, reverse=True):
    print(f"n={n:4d} ({100*n/len(df):4.1f}%) | median fc/out {med:6.2f} | "
          f"within20 if corrected by group median {cw:.2f} | {rule}")
print("\nTREND: mean log(fc_over_p2p) by year (positive = over-forecast)")
print("  overall:", {int(k): round(v,2) for k,v in
      pd.Series(np.log(base)).groupby(yr).mean().items()})
for n, med, cw, rule, msk in sorted(stats, reverse=True)[:8]:
    d = {int(k): round(v,2) for k,v in
         pd.Series(np.log(base[msk])).groupby(yr[msk]).mean().items()}
    print(f"  n={n:4d}: {d} | {rule[:90]}")
