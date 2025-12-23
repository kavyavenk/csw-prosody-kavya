#!/usr/bin/env python3
"""
Run statistical comparisons for MASAC using existing prosodic features.

Note: Uses 12 basic prosodic features (not DisVoice 103) due to scipy compatibility issues.
"""

import argparse
import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
import statsmodels.stats.multitest as smm

p = argparse.ArgumentParser()
p.add_argument("--features-file", type=str,
               default="features/masac_prosodic_features.csv",
               help="Path to prosodic features CSV")
args = p.parse_args()

FEAT = args.features_file
df = pd.read_csv(FEAT)

# Get feature columns (exclude metadata columns)
feature_cols = [c for c in df.columns if c not in ["utt_id", "file_id", "speaker", "lang", "condition"]]

print(f"Analyzing {len(feature_cols)} prosodic features")
print(f"Features: {', '.join(feature_cols)}")

def run_compare(a_mask, b_mask, label):
    a = df.loc[a_mask, feature_cols]
    b = df.loc[b_mask, feature_cols]
    pvals, ds = [], []
    
    for c in feature_cols:
        aa, bb = a[c].dropna(), b[c].dropna()
        if len(aa) < 5 or len(bb) < 5:
            pvals.append(np.nan)
            ds.append(np.nan)
            continue
        
        # Welch's t-test (unequal variances)
        t, p = ttest_ind(aa, bb, equal_var=False)
        pvals.append(p)
        
        # Cohen's d
        s = np.sqrt(((aa.var(ddof=1)*(len(aa)-1)) + (bb.var(ddof=1)*(len(bb)-1))) / (len(aa)+len(bb)-2))
        ds.append((aa.mean()-bb.mean())/s if s>0 else np.nan)
    
    pvals = np.array(pvals, float)
    mask = ~np.isnan(pvals)
    padj = np.full_like(pvals, np.nan, dtype=float)
    
    if mask.any():
        padj[mask] = smm.multipletests(pvals[mask], alpha=0.05, method="fdr_bh")[1]
    
    out = pd.DataFrame({
        "feature": feature_cols,
        "p": pvals,
        "p_adj": padj,
        "cohen_d": ds
    })
    out["sig"] = out["p_adj"] < 0.05
    out = out.sort_values("p_adj")
    
    out_file = f"features/first_contrast_masac_{label}.csv"
    out.to_csv(out_file, index=False)
    
    n_sig = int(out["sig"].sum())
    print(f"\n[{label}] Significant features: {n_sig} / {len(out)} ({100*n_sig/len(out):.1f}%)")
    
    return out

# Run comparisons
cs = df["condition"] == "code_switched"
mono_en = df["condition"] == "monolingual_EN"
mono_hi = df["condition"] == "monolingual_HI"

print(f"\nData distribution:")
print(f"  CSW: {cs.sum()}")
print(f"  EN: {mono_en.sum()}")
print(f"  HI: {mono_hi.sum()}")

print("\n" + "="*60)
print("Running CSW vs Monolingual English comparison...")
print("="*60)
run_compare(cs, mono_en, "CS_vs_EN")

print("\n" + "="*60)
print("Running CSW vs Monolingual Hindi comparison...")
print("="*60)
run_compare(cs, mono_hi, "CS_vs_HI")

print("\n" + "="*60)
print("Analysis complete!")
print("Results saved to:")
print("  - features/first_contrast_masac_CS_vs_EN.csv")
print("  - features/first_contrast_masac_CS_vs_HI.csv")
print("="*60)

