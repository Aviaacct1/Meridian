"""(1) Distil complete-substrate NEW-feature M1 into named subgroups, with
the 80/20 goal in view. (2) Era divergence: where does the pre-trained M2b
misread 2024?"""
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor, _tree
from sklearn.model_selection import GroupKFold

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
NUMS = ["gcd_km","natural","seats_market","capacity","avg_fare"] + AIRPORT + NEWF
FEATS = NUMS + CAT

def prep(df):
    df = df[(df.fc_over_p2p.notna()) & (df.fc_over_p2p > 0)
            & (df.natural >= df.p2p_outturn) & (df.p2p_outturn > 0)
            & (df.capacity > 0)].reset_index(drop=True)
    for c in CAT:
        df[c] = df[c].astype(str)
        vc = df[c].value_counts()
        df.loc[df[c].isin(vc[vc < 5].index), c] = "OTHER"
        df[c] = df[c].astype("category")
    return df

dC = prep(pd.read_csv(APP + "master_complete.csv"))
X = dC[FEATS]
y1 = np.log(dC.fc_over_p2p.values)
base = dC.fc_over_p2p.values
m = HistGradientBoostingRegressor(
    learning_rate=0.05, max_iter=2000, max_leaf_nodes=15,
    min_samples_leaf=40, l2_regularization=1.0, early_stopping=True,
    validation_fraction=0.15, n_iter_no_change=30,
    categorical_features=CAT, random_state=0)
m.fit(X, y1)
pred = m.predict(X)

Xd = pd.get_dummies(X, columns=CAT)
dt = DecisionTreeRegressor(max_depth=4, min_samples_leaf=40, random_state=0)
dt.fit(Xd, pred)
tree = dt.tree_; fnames = Xd.columns.to_numpy()

def rules(node=0, conds=(), out=None):
    out = out if out is not None else []
    if tree.children_left[node] == _tree.TREE_LEAF:
        out.append((conds, node)); return out
    f, t = fnames[tree.feature[node]], tree.threshold[node]
    if f in NUMS:
        lo, hi = f"{f}<={t:,.2f}", f"{f}>{t:,.2f}"
    else:
        lo, hi = f"NOT {f}", f"{f}"
    rules(tree.children_left[node], conds + (lo,), out)
    rules(tree.children_right[node], conds + (hi,), out)
    return out

leaf = dt.apply(Xd)
w20 = lambda r: float(np.mean((r >= 0.8) & (r <= 1.2)))
print("SUBGROUPS, complete substrate NEW features (M1 correction distilled)")
stats = []
for conds, node in rules():
    msk = leaf == node
    n = int(msk.sum()); med = float(np.median(base[msk]))
    stats.append((n, med, w20(base[msk]/med), " & ".join(conds)))
for n, med, cw, rule in sorted(stats, reverse=True):
    print(f"n={n:3d} ({100*n/len(dC):4.1f}%) | med fc/out {med:5.2f} | "
          f"w20 if median-corrected {cw:.2f} | {rule}")

# ---- era divergence on scored file: transfer model residuals by segment ----
dS = prep(pd.read_csv(APP + "master_backtest_scored.csv"))
state = pickle.load(open("/tmp/qsi2_state.pkl", "rb"))
post = (dS.year >= 2020).values
s = state[("S", "M2b", "OLD", "transfer", 0)]
r = dS.capacity.values[post] * np.exp(s["pred_te"]) / dS.p2p_outturn.values[post]
dpost = dS[post].copy(); dpost["lr"] = np.log(r)
print("\n2024 DIVERGENCE: mean log(model/actual) of pre-trained M2b on 2024 "
      "(negative = 2024 outturn higher than pre-era relationship predicts)")
for col in ["type", "haul_band", "service", "domestic", "region"]:
    g = dpost.groupby(col, observed=True)["lr"].agg(["mean", "count"])
    g = g[g["count"] >= 25].round(2)
    print(f"  by {col}: " + ", ".join(f"{i}={v['mean']:+.2f}(n={int(v['count'])})"
          for i, v in g.iterrows()))
