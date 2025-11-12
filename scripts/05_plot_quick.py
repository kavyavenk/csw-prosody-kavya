import argparse, pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--corpus", choices=["masac","seame"], required=True)
args = p.parse_args()

def family(name):
    n = name.lower()
    if "f0" in n or "pitch" in n:
        return "pitch"
    if "energy" in n or "intensity" in n:
        return "energy"
    if "dur" in n or "duration" in n or "rate" in n or "rhythm" in n:
        return "duration"
    return "other"

def plot_sig_share(contrast_csv, title):
    df = pd.read_csv(contrast_csv)
    if "sig" not in df.columns:
        df["sig"] = df["p_adj"] < 0.05
    df["family"] = df["feature"].map(family)
    grp = df.groupby("family")["sig"].mean().reset_index()
    plt.figure()
    plt.bar(grp["family"], grp["sig"]*100.0)
    plt.title(title + " — % significant by family")
    plt.ylabel("% significant")
    plt.xlabel("family")
    plt.tight_layout()
    out = Path(contrast_csv).with_suffix(".png")
    plt.savefig(out, dpi=160)
    print("Saved", out)

def plot_top_effects(contrast_csv, title, k=10):
    df = pd.read_csv(contrast_csv)
    df = df.dropna(subset=["cohen_d"])
    df = df.nsmallest(k, "p_adj")
    plt.figure()
    plt.barh(df["feature"], df["cohen_d"])
    plt.title(title + f" — Top {k} features by significance")
    plt.xlabel("Cohen's d (CS - mono)")
    plt.tight_layout()
    out = Path(contrast_csv).with_name(Path(contrast_csv).stem + "_top.png")
    plt.savefig(out, dpi=160)
    print("Saved", out)

label = "masac" if args.corpus=="masac" else "seame"
csv = f"features/first_contrast_{label}.csv"
if Path(csv).exists():
    plot_sig_share(csv, label.upper())
    plot_top_effects(csv, label.upper(), k=10)
else:
    print("Missing", csv, "- run contrasts first.")
