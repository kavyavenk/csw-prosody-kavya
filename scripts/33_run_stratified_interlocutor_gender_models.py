#!/usr/bin/env python3
"""
Run stratified interlocutor-gender prosody models (SEAME).

IMPORTANT: We **do not recompute** interlocutor labels inside each stratum, because
subsetting changes turn order. Instead we:
- load the integrated features CSV
- merge in precomputed labels from `seame_interlocutor_gender_labels.csv`
- then subset by speaker gender / age_bucket and fit models.
"""

from __future__ import annotations

import argparse
import pathlib
from typing import List

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


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


def _lhs(col: str) -> str:
    if col.isidentifier():
        return col
    esc = str(col).replace("\\", "\\\\").replace('"', '\\"')
    return f'Q("{esc}")'


def _fit_models(df: pd.DataFrame, outcomes: List[str], group_var: str) -> pd.DataFrame:
    rows = []
    for y in outcomes:
        keep = [y, "gender_match", "condition", "duration_sec", group_var]
        d = df[keep].replace([np.inf, -np.inf], np.nan).dropna()
        if len(d) < 500:
            rows.append({"feature": y, "success": False, "error": "insufficient_data"})
            continue
        d["gender_match"] = pd.Categorical(d["gender_match"].astype(str), ["same", "different", "unknown"])
        formula = (
            f"{_lhs(y)} ~ C(gender_match, Treatment(reference='same')) + C(condition) + duration_sec"
        )
        try:
            res = smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": d[group_var]})
        except Exception as e:
            rows.append({"feature": y, "success": False, "error": str(e)})
            continue

        key = "C(gender_match, Treatment(reference='same'))[T.different]"
        rows.append(
            {
                "feature": y,
                "success": True,
                "n_obs": len(d),
                "n_groups": int(d[group_var].nunique()),
                "coef_diff_vs_same": float(res.params.get(key, np.nan)),
                "p_diff_vs_same": float(res.pvalues.get(key, np.nan)),
            }
        )
    return pd.DataFrame(rows)


def _run_one_stratum(df: pd.DataFrame, out_dir: pathlib.Path, n_features: int, group_var: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    outcomes = _select_numeric_features(df, n_features)
    models = _fit_models(df, outcomes, group_var=group_var)
    models.to_csv(out_dir / "seame_interlocutor_gender_models.csv", index=False)

    # Save label distribution for this stratum
    gm = df["gender_match"].value_counts(dropna=False).rename_axis("gender_match").reset_index(name="count")
    gm.to_csv(out_dir / "gender_match_counts.csv", index=False)


def main() -> None:
    p = argparse.ArgumentParser(description="Run stratified SEAME interlocutor-gender models")
    p.add_argument(
        "--input",
        type=str,
        default="results/functional_anchors/seame/seame_integrated_features.csv",
        help="SEAME integrated features CSV",
    )
    p.add_argument(
        "--labels",
        type=str,
        default="results/interlocutor_gender/seame_final/seame_interlocutor_gender_labels.csv",
        help="Precomputed interlocutor gender labels CSV (from scripts/30_interlocutor_gender_effects.py)",
    )
    p.add_argument(
        "--out-root",
        type=str,
        default="results/interlocutor_gender/seame_stratified",
        help="Output root directory",
    )
    p.add_argument("--n-features", type=int, default=20)
    p.add_argument("--group-var", type=str, default="speaker")
    args = p.parse_args()

    df = pd.read_csv(args.input, low_memory=False)
    labels = pd.read_csv(args.labels, low_memory=False)
    labels = labels[["utt_id", "gender_match"]].copy()
    df = df.merge(labels, on="utt_id", how="left", validate="1:1")
    df["gender_match"] = df["gender_match"].fillna("unknown").astype(str)

    out_root = pathlib.Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    # Strata definitions
    # Gender strata
    for g in ["female", "male"]:
        sub = df[df["gender"].astype(str).str.lower() == g].copy()
        if len(sub) < 500:
            continue
        _run_one_stratum(sub, out_root / f"gender={g}", int(args.n_features), str(args.group_var))

    # Age bucket strata (SEAME buckets)
    if "age_bucket" in df.columns:
        for ab in sorted(df["age_bucket"].dropna().astype(str).unique().tolist()):
            sub = df[df["age_bucket"].astype(str) == ab].copy()
            if len(sub) < 500:
                continue
            _run_one_stratum(sub, out_root / f"age_bucket={ab}", int(args.n_features), str(args.group_var))


if __name__ == "__main__":
    main()

