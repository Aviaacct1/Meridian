"""Score runner2 checkpoints: complete-substrate OLD vs NEW, and era work."""
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

STATE = "/tmp/qsi2_state.pkl"
APP = "/sessions/happy-hopeful-brahmagupta/mnt/app/"
CAT = ["haul_band","domestic","dep_country","arr_country","region",
       "type","carrier","hub_dest","service","seats_market_band"]

def load(path):
    df = pd.read_csv(APP + path)
    df = df[(df.fc_over_p2p.notna()) & (df.fc_over_p2p > 0)
            & (df.natural >= df.p2p_outturn) & (df.p2p_outturn > 0)
            & (df.capacity > 0)].reset_index(drop=True)
    return df

dC = load("master_complete.csv")
dS = load("master_backtest_scored.csv")

def gfolds(df, n=5):
    out = []
    gkf = GroupKFold(n_splits=n)
    for k, (tr, te) in enumerate(gkf.split(df, groups=df.dep.values)):
        m_tr = np.zeros(len(df), bool); m_tr[tr] = True
        m_te = np.zeros(len(df), bool); m_te[te] = True
        out.append((k, m_tr, m_te))
    return out

pre_S = (dS.year < 2020).values; post_S = ~pre_S
foldsC = [("temporal", 0, (dC.year == 2017).values, (dC.year == 2018).values)] \
       + [("grouped", k, tr, te) for k, tr, te in gfolds(dC)]
foldsS = [("grouped", k, tr, te) for k, tr, te in gfolds(dS)] \
       + [("transfer", 0, pre_S, post_S)]
for era, msk in [("pre", pre_S), ("post", post_S)]:
    sub = dS[msk]
    for k, tr, te in gfolds(sub):
        g_tr = np.zeros(len(dS), bool); g_tr[np.where(msk)[0][tr]] = True
        g_te = np.zeros(len(dS), bool); g_te[np.where(msk)[0][te]] = True
        foldsS.append((era, k, g_tr, g_te))

state = pickle.load(open(STATE, "rb"))
w20 = lambda r: float(np.mean((r >= 0.8) & (r <= 1.2)))
slog = lambda r: float(np.std(np.log(np.clip(r, 1e-9, None))))

def ratio(df, mod, pred, idx):
    base = df.fc_over_p2p.values; cap = df.capacity.values
    p2p = df.p2p_outturn.values
    shr = np.clip(base * p2p / np.clip(df.forecast_pax.values, 1e-9, None), 0, 1)
    if mod == "M1":  return base[idx] / np.exp(pred)
    if mod == "M2a": return cap[idx] * np.exp(pred) * shr[idx] / p2p[idx]
    if mod == "M2b": return cap[idx] * np.exp(pred) / p2p[idx]

bC = dC.fc_over_p2p.values; bS = dS.fc_over_p2p.values
print(f"COMPLETE substrate n={len(dC)} (2017-18) baseline w20 "
      f"{w20(bC):.3f} sigma {slog(bC):.3f}; 2018 only {w20(bC[(dC.year==2018)]):.3f}")
print(f"SCORED substrate  n={len(dS)} baseline: pre {w20(bS[pre_S]):.3f} "
      f"(n={pre_S.sum()}), post-2024 {w20(bS[post_S]):.3f} (n={post_S.sum()})")

print("\n-- COMPLETE substrate: OLD vs NEW features --")
for mod in ["M1", "M2a", "M2b"]:
    for fs in ["OLD", "NEW"]:
        for split in ["temporal", "grouped"]:
            fits, rats = [], []
            for (fn, k, tr, te) in foldsC:
                key = ("C", mod, fs, fn, k)
                if fn != split or key not in state: continue
                s = state[key]
                fits.append(w20(ratio(dC, mod, s["pred_tr"], tr)))
                rats.append(ratio(dC, mod, s["pred_te"], te))
            if not rats: continue
            r = np.concatenate(rats)
            print(f"{mod:4s} {fs:3s} {split:9s} fit {np.mean(fits):.3f} | "
                  f"held-out {w20(r):.3f} (gap {np.mean(fits)-w20(r):+.3f}) | "
                  f"sigma {slog(r):.3f} | n {len(r)}")

print("\n-- SCORED substrate: era analysis (OLD features) --")
for mod in ["M1", "M2a", "M2b"]:
    rats_all, prs, pos = [], [], []
    for (fn, k, tr, te) in foldsS:
        key = ("S", mod, "OLD", fn, k)
        if fn != "grouped" or key not in state: continue
        s = state[key]
        r = ratio(dS, mod, s["pred_te"], te)
        rats_all.append(r); prs.append(r[pre_S[te]]); pos.append(r[post_S[te]])
    if not rats_all: continue
    ra = np.concatenate(rats_all)
    rp = np.concatenate(prs); ro = np.concatenate(pos)
    print(f"{mod:4s} grouped-all w20 {w20(ra):.3f} | pre rows {w20(rp):.3f} "
          f"(n={len(rp)}) | post rows {w20(ro):.3f} (n={len(ro)})")
for mod in ["M1", "M2b"]:
    key = ("S", mod, "OLD", "transfer", 0)
    if key in state:
        s = state[key]
        r = ratio(dS, mod, s["pred_te"], post_S)
        rf = ratio(dS, mod, s["pred_tr"], pre_S)
        print(f"{mod:4s} TRANSFER train-pre->test-2024: fit(pre) {w20(rf):.3f} "
              f"| 2024 held-out {w20(r):.3f} | sigma {slog(r):.3f} | n {len(r)}")
for era in ["pre", "post"]:
    rats = []
    for (fn, k, tr, te) in foldsS:
        key = ("S", "M2b", "OLD", fn, k)
        if fn != era or key not in state: continue
        rats.append(ratio(dS, "M2b", state[key]["pred_te"], te))
    if rats:
        r = np.concatenate(rats)
        print(f"M2b within-{era:4s} grouped CV: held-out w20 {w20(r):.3f} | "
              f"sigma {slog(r):.3f} | n {len(r)}")
