"""Score all models from the checkpointed predictions."""
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

STATE = "/tmp/qsi_state.pkl"
PATH = "/sessions/happy-hopeful-brahmagupta/mnt/app/master_backtest_scored.csv"

df = pd.read_csv(PATH)
df = df[(df.fc_over_p2p.notna()) & (df.fc_over_p2p > 0)
        & (df.natural >= df.p2p_outturn) & (df.p2p_outturn > 0)
        & (df.capacity > 0)].reset_index(drop=True)

base = df.fc_over_p2p.values
cap = df.capacity.values
p2p = df.p2p_outturn.values
fc_p2p = df.fc_over_p2p.values * df.p2p_outturn.values  # engine forecast P2P
p2p_share_fc = np.clip(fc_p2p / np.clip(df.forecast_pax.values, 1e-9, None), 0, 1)

te_t = (df.year == 2018).values
folds = [("temporal", 0, ~te_t, te_t)]
gkf = GroupKFold(n_splits=5)
y1 = np.log(base)
for k, (tr, te) in enumerate(gkf.split(df, y1, groups=df.dep.values)):
    m_tr = np.zeros(len(df), bool); m_tr[tr] = True
    m_te = np.zeros(len(df), bool); m_te[te] = True
    folds.append(("grouped", k, m_tr, m_te))

state = pickle.load(open(STATE, "rb"))
w20 = lambda r: float(np.mean((r >= 0.8) & (r <= 1.2)))
slog = lambda r: float(np.std(np.log(np.clip(r, 1e-9, None))))

def ratio(mod, pred, idx):
    if mod in ("M1", "M1y"):
        return base[idx] / np.exp(pred)
    if mod == "M2a":
        return cap[idx] * np.exp(pred) * p2p_share_fc[idx] / p2p[idx]
    if mod == "M2b":
        return cap[idx] * np.exp(pred) / p2p[idx]

print(f"BASELINE uncorrected: within20 all {w20(base):.3f} | "
      f"2018 test year {w20(base[te_t]):.3f} | sigma_log {slog(base):.3f} | "
      f"n={len(df)}, n2018={int(te_t.sum())}")

for mod in ["M1", "M2a", "M2b", "M1y"]:
    for split in ["temporal", "grouped"]:
        fit_shares, ratios = [], []
        for (fn, k, tr, te) in folds:
            if fn != split or (mod, fn, k) not in state:
                continue
            s = state[(mod, fn, k)]
            fit_shares.append(w20(ratio(mod, s["pred_tr"], tr)))
            ratios.append(ratio(mod, s["pred_te"], te))
        if not ratios:
            continue
        r = np.concatenate(ratios)
        print(f"{mod:4s} {split:9s} fit {np.mean(fit_shares):.3f} | "
              f"held-out {w20(r):.3f} (gap {np.mean(fit_shares)-w20(r):+.3f}) | "
              f"sigma_log after {slog(r):.3f} | n {len(r)}")
