"""Score round-3 checkpoints + mechanism checks + 2024 trim question."""
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

STATE = "/tmp/qsi3_state.pkl"
PATH = ("/sessions/happy-hopeful-brahmagupta/mnt/app/"
        "master_v2_complete_dot.csv")

df = pd.read_csv(PATH)
df = df[(df.fc_over_p2p.notna()) & (df.fc_over_p2p > 0)
        & (df.natural >= df.p2p_outturn) & (df.p2p_outturn > 0)
        & (df.capacity > 0)].reset_index(drop=True)

base = df.fc_over_p2p.values
cap = df.capacity.values
p2p = df.p2p_outturn.values
shr = np.clip(base * p2p / np.clip(df.forecast_pax.values, 1e-9, None), 0, 1)

te_t = (df.year == 2024).values
folds = [("temporal", 0, ~te_t, te_t)]
gkf = GroupKFold(n_splits=5)
for k, (tr, te) in enumerate(gkf.split(df, groups=df.dep.values)):
    m_tr = np.zeros(len(df), bool); m_tr[tr] = True
    m_te = np.zeros(len(df), bool); m_te[te] = True
    folds.append(("grouped", k, m_tr, m_te))

state = pickle.load(open(STATE, "rb"))
w20 = lambda r: float(np.mean((r >= 0.8) & (r <= 1.2)))
slog = lambda r: float(np.std(np.log(np.clip(r, 1e-9, None))))

def ratio(mod, pred, idx):
    if mod == "M1":  return base[idx] / np.exp(pred)
    if mod == "M2a": return cap[idx] * np.exp(pred) * shr[idx] / p2p[idx]
    if mod == "M2b": return cap[idx] * np.exp(pred) / p2p[idx]

print(f"BASELINE: w20 all {w20(base):.3f} | 2024 {w20(base[te_t]):.3f} | "
      f"sigma {slog(base):.3f} | n={len(df)}, n2024={int(te_t.sum())}")
oof = {}
for mod in ["M1", "M2a", "M2b"]:
    for split in ["temporal", "grouped"]:
        fits, rats, tes = [], [], []
        for (fn, k, tr, te) in folds:
            if fn != split or (mod, fn, k) not in state:
                continue
            s = state[(mod, fn, k)]
            fits.append(w20(ratio(mod, s["pred_tr"], tr)))
            rats.append(ratio(mod, s["pred_te"], te))
            tes.append(te)
        r = np.concatenate(rats)
        if split == "grouped":
            o = np.full(len(df), np.nan)
            for rr, te in zip(rats, tes):
                o[te] = rr
            oof[mod] = o
        print(f"{mod:4s} {split:9s} fit {np.mean(fits):.3f} | "
              f"held-out {w20(r):.3f} (gap {np.mean(fits)-w20(r):+.3f}) | "
              f"sigma {slog(r):.3f} | n {len(r)}")

# 2024 trim question: bias of temporal M2b on 2024
s = state[("M2b", "temporal", 0)]
r24 = ratio("M2b", s["pred_te"], te_t)
print(f"\n2024 cold test, M2b: mean log(model/actual) {np.mean(np.log(r24)):+.3f} "
      f"| w20 {w20(r24):.3f} | after uniform trim of the mean bias: "
      f"{w20(r24/np.exp(np.mean(np.log(r24)))):.3f}")
d24 = df[te_t]
for col in ["type", "haul_band", "domestic"]:
    g = pd.Series(np.log(r24)).groupby(d24[col].values).agg(["mean","count"])
    g = g[g["count"] >= 20].round(2)
    print(f"  2024 bias by {col}: " + ", ".join(
        f"{i}={v['mean']:+.2f}(n={int(v['count'])})" for i, v in g.iterrows()))

# mechanism cells at scale
cells = {
 "OVER-READ planned_lf>0.42 & d_captured>34.6k":
    (df.planned_lf > 0.42) & (df.d_captured > 34642),
 "UNDER-READ capture_rate<=0.24 & planned_lf<=0.05":
    (df.capture_rate <= 0.24) & (df.planned_lf <= 0.05)}
print("\nENGINE-MECHANISM CELLS at full scale:")
for name, msk in cells.items():
    n = int(msk.sum())
    print(f"  {name}: n={n} ({100*n/len(df):.1f}%) | median fc/p2p "
          f"{np.median(base[msk]):.2f} | baseline w20 {w20(base[msk]):.2f} | "
          f"M1-corrected OOF w20 {w20(oof['M1'][msk]):.2f} | "
          f"M2b OOF w20 {w20(oof['M2b'][msk]):.2f}")
