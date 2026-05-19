#!/usr/bin/env python3
"""
Age-only main-effects analysis on prosodic outcomes (no interlocutor predictors).

Fits (OLS with clustered SEs by speaker):
  outcome ~ C(age_bucket) + C(gender) + C(condition) [+ duration_sec if present]

For SEAME: age_bucket levels are expected like <19, 19-24, 25+ (reference default: 19-24).
For MASAC: age_bucket levels are expected like Younger, Older (reference default: Older).

Outputs:
- `models_age_main.csv`: per-outcome coefficients + p-values for age contrasts
- `models_age_main_fdr.csv`: same plus BH-FDR adjusted p-values for the age terms
- `age_main_summary.md`: short narrative summary with key directions
"""

from __future__ import annotations

import argparse
import pathlib
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests


def _lhs(col: str) -> str:
    if col.isidentifier():
        return col
    esc = str(col).replace("\\", "\\\\").replace('"', '\\"')
    return f'Q("{esc}")'


def _select_numeric_features(df: pd.DataFrame, n: int) -> List[str]:
    exclude = {
        "start",
        "end",
        "start_time",
        "end_time",
        "duration_sec",
        "n_switches",
        "n_discourse_markers",
        "n_repetitions",
        "audience_l2_ratio",
    }
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    candidates = [c for c in numeric if c not in exclude]
    if not candidates:
        return []
    var = df[candidates].var(numeric_only=True).sort_values(ascending=False)
    return var.head(n).index.tolist()


def _fit_one(
    df: pd.DataFrame,
    outcome: str,
    age_ref: str,
    speaker_col: str,
) -> Tuple[bool, Dict[str, object]]:
    cols = [outcome, "age_bucket", "gender", "condition", speaker_col]
    has_dur = "duration_sec" in df.columns
    if has_dur:
        cols.append("duration_sec")

    d = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) < 500:
        return False, {"error": "insufficient_data", "n_obs": len(d)}

    # Ensure types
    d["age_bucket"] = d["age_bucket"].astype(str)
    d["gender"] = d["gender"].astype(str)
    d["condition"] = d["condition"].astype(str)

    rhs = [
        f"C(age_bucket, Treatment(reference='{age_ref}'))",
        "C(gender)",
        "C(condition)",
    ]
    if has_dur:
        rhs.append("duration_sec")
    formula = f"{_lhs(outcome)} ~ " + " + ".join(rhs)

    try:
        res = smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": d[speaker_col]})
    except Exception as e:
        return False, {"error": str(e), "n_obs": len(d)}

    out: Dict[str, object] = {
        "feature": outcome,
        "success": True,
        "n_obs": int(len(d)),
        "n_speakers": int(d[speaker_col].nunique()),
        "age_ref": age_ref,
        "formula": formula,
    }

    # Pull all age_bucket params/pvals
    for term, coef in res.params.items():
        if term.startswith("C(age_bucket"):
            out[f"coef::{term}"] = float(coef)
    for term, pv in res.pvalues.items():
        if term.startswith("C(age_bucket"):
            out[f"p::{term}"] = float(pv)

    return True, out


def _bh_fdr_adjust(df: pd.DataFrame) -> pd.DataFrame:
    # Apply BH-FDR across all age-term p-values across outcomes
    p_cols = [c for c in df.columns if c.startswith("p::C(age_bucket")]
    if not p_cols:
        return df

    long = []
    for i, row in df.iterrows():
        if not bool(row.get("success", False)):
            continue
        for pc in p_cols:
            pv = row.get(pc)
            if pv is None or (isinstance(pv, float) and np.isnan(pv)):
                continue
            long.append((i, pc, float(pv)))

    if not long:
        return df

    pvals = np.array([x[2] for x in long], dtype=float)
    _, p_adj, _, _ = multipletests(pvals, alpha=0.05, method="fdr_bh")

    df2 = df.copy()
    for (i, pc, _pv), pa in zip(long, p_adj):
        df2.loc[i, pc.replace("p::", "p_adj_fdr::")] = float(pa)
        df2.loc[i, pc.replace("p::", "sig_fdr_0_05::")] = bool(pa < 0.05)

    return df2


def _narrative(df_fdr: pd.DataFrame, title: str, age_ref: str) -> str:
    p_adj_cols = [c for c in df_fdr.columns if c.startswith("p_adj_fdr::C(age_bucket")]
    coef_cols = [c for c in df_fdr.columns if c.startswith("coef::C(age_bucket")]

    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- Age reference level: `{age_ref}`")
    lines.append(f"- Outcomes modeled: {int(df_fdr['success'].fillna(False).sum())} (requested top-variance set)")
    lines.append("")

    if not p_adj_cols:
        lines.append("No age_bucket term p-values were found to adjust.")
        return "\n".join(lines)

    # Count significant terms
    sig_cols = [c for c in df_fdr.columns if c.startswith("sig_fdr_0_05::C(age_bucket")]
    sig_total = 0
    if sig_cols:
        sig_total = int(df_fdr[sig_cols].fillna(False).to_numpy().sum())
    lines.append(f"- Significant age terms after BH-FDR (α=0.05): **{sig_total}** (term-level, across outcomes)")
    lines.append("")

    # Show top 10 smallest adjusted p-values
    long = []
    for _, row in df_fdr[df_fdr.get("success", False) == True].iterrows():
        feat = row["feature"]
        for pc in p_adj_cols:
            pa = row.get(pc)
            if pa is None or (isinstance(pa, float) and np.isnan(pa)):
                continue
            term = pc.replace("p_adj_fdr::", "")
            coef_key = "coef::" + term
            coef = row.get(coef_key)
            long.append((feat, term, float(coef) if coef is not None else np.nan, float(pa)))

    long.sort(key=lambda x: x[3])
    top = long[:10]
    if top:
        lines.append("## Top age effects (lowest FDR-adjusted p-values)")
        for feat, term, coef, pa in top:
            direction = "higher" if coef > 0 else "lower"
            lines.append(f"- **{feat}**: `{term}` → {direction} by {coef:.3g} (p_adj={pa:.3g})")
        lines.append("")

    lines.append("## Interpretation notes")
    lines.append("- Coefficients are differences vs the reference age bucket, controlling for gender and condition (and duration if available).")
    lines.append("- These are **age main effects** (not interlocutor effects).")
    return "\n".join(lines)


def run(
    input_csv: pathlib.Path,
    out_dir: pathlib.Path,
    n_features: int,
    age_ref: str,
    speaker_col: str = "speaker",
    drop_unknown_age: bool = True,
) -> None:
    df = pd.read_csv(input_csv, low_memory=False)
    for c in ["age_bucket", "gender", "condition", speaker_col]:
        if c not in df.columns:
            raise ValueError(f"Missing required column `{c}` in {input_csv}")

    if drop_unknown_age:
        df = df[df["age_bucket"].astype(str).ne("unknown")].copy()

    out_dir.mkdir(parents=True, exist_ok=True)

    outcomes = _select_numeric_features(df, n_features)
    rows = []
    for y in outcomes:
        ok, rec = _fit_one(df, y, age_ref=age_ref, speaker_col=speaker_col)
        rec["feature"] = y
        rec["success"] = bool(ok)
        rows.append(rec)

    res = pd.DataFrame(rows)
    res.to_csv(out_dir / "models_age_main.csv", index=False)

    res_fdr = _bh_fdr_adjust(res)
    res_fdr.to_csv(out_dir / "models_age_main_fdr.csv", index=False)

    title = f"Age main effects – {input_csv.name}"
    (out_dir / "age_main_summary.md").write_text(_narrative(res_fdr, title=title, age_ref=age_ref), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Age-only main effects on prosodic outcomes")
    p.add_argument("--input", type=str, required=True)
    p.add_argument("--out-dir", type=str, required=True)
    p.add_argument("--n-features", type=int, default=30, help="Top-variance outcomes to model")
    p.add_argument("--age-ref", type=str, required=True, help="Reference age bucket label")
    p.add_argument("--speaker-col", type=str, default="speaker", help="Cluster/group column (speaker)")
    p.add_argument(
        "--keep-unknown-age",
        action="store_true",
        help="If set, do not drop age_bucket=='unknown' rows before modeling",
    )
    args = p.parse_args()

    run(
        input_csv=pathlib.Path(args.input),
        out_dir=pathlib.Path(args.out_dir),
        n_features=int(args.n_features),
        age_ref=str(args.age_ref),
        speaker_col=str(args.speaker_col),
        drop_unknown_age=not bool(args.keep_unknown_age),
    )

