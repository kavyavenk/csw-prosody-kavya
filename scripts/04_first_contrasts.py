import argparse, pandas as pd, numpy as np, pathlib
from scipy.stats import ttest_ind
import statsmodels.stats.multitest as smm

p = argparse.ArgumentParser()
p.add_argument("--corpus", choices=["masac","seame"], required=True)
args = p.parse_args()

FEAT = f"features/{args.corpus}_disvoice_utt.csv"
if not pathlib.Path(FEAT).exists():
    raise SystemExit(f"Feature file not found: {FEAT}")
df = pd.read_csv(FEAT)

feature_cols = [c for c in df.columns if c not in ["utt_id","speaker","lang","condition"]]

def run_compare(a_mask, b_mask, label):
    a = df.loc[a_mask, feature_cols]
    b = df.loc[b_mask, feature_cols]
    pvals, ds = [], []
    for c in feature_cols:
        aa, bb = a[c].dropna(), b[c].dropna()
        if len(aa) < 5 or len(bb) < 5:
            pvals.append(np.nan); ds.append(np.nan); continue
        t, p = ttest_ind(aa, bb, equal_var=False)
        pvals.append(p)
        s = np.sqrt(((aa.var(ddof=1)*(len(aa)-1)) + (bb.var(ddof=1)*(len(bb)-1))) / (len(aa)+len(bb)-2))
        ds.append((aa.mean()-bb.mean())/s if s>0 else np.nan)
    pvals = np.array(pvals, float)
    mask = ~np.isnan(pvals)
    padj = np.full_like(pvals, np.nan, dtype=float)
    if mask.any():
        padj[mask] = smm.multipletests(pvals[mask], alpha=0.05, method="fdr_bh")[1]
    out = pd.DataFrame({"feature": feature_cols, "p": pvals, "p_adj": padj, "cohen_d": ds})
    out["sig"] = out["p_adj"] < 0.05
    out = out.sort_values("p_adj")
    out_file = f"features/first_contrast_{args.corpus}_{label}.csv"
    out.to_csv(out_file, index=False)
    print(f"[{args.corpus}] {label}: n_sig:", int(out["sig"].sum()), "/", len(out))
    return out

if args.corpus == "masac":
    cs = df["condition"]=="code_switched"
    mono_en = df["condition"]=="monolingual_EN"
    mono_hi = df["condition"]=="monolingual_HI"
    run_compare(cs, mono_en, "CS_vs_EN")
    run_compare(cs, mono_hi, "CS_vs_HI")
else:
    cs = df["condition"]=="code_switched"
    mono_en = df["condition"]=="monolingual_EN"
    mono_zh = df["condition"]=="monolingual_ZH"
    run_compare(cs, mono_en, "CS_vs_EN")
    run_compare(cs, mono_zh, "CS_vs_ZH")
print("Wrote contrast CSVs under features/")
