#!/usr/bin/env python3
"""
Run interlocutor-gender models with age_bucket effects (MASAC, optionally SEAME).

We use precomputed interlocutor labels by reusing `scripts/30_interlocutor_gender_effects.py`
as a labeler, then fit OLS with clustered SEs:

Outcome ~ gender_match * age_bucket + condition + duration_sec

Outputs:
- CSV of coefficients/p-values for:
  - gender_match[T.different]
  - age_bucket levels (vs reference)
  - gender_match[T.different]:age_bucket interactions
"""

from __future__ import annotations

import argparse
import pathlib
import importlib.util
import sys
from typing import List

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


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


def _load_labeler(repo_root: pathlib.Path):
    script_path = repo_root / "scripts" / "30_interlocutor_gender_effects.py"
    spec = importlib.util.spec_from_file_location("interlocutor_gender_effects", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {script_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def add_labels(df: pd.DataFrame, repo_root: pathlib.Path) -> pd.DataFrame:
    labeler = _load_labeler(repo_root)
    # Reuse internal helper that computes gender_match etc.
    # We call add_interlocutor_gender directly, preserving ordering logic in run().
    tmp = df.copy()
    order_col = None
    if "start_time" not in tmp.columns and "end_time" not in tmp.columns and "utt_id" in tmp.columns:
        parts = tmp["utt_id"].astype(str).str.rsplit("_", n=1, expand=True)
        if parts.shape[1] == 2:
            tmp["_utt_ord"] = pd.to_numeric(parts[1], errors="coerce")
            order_col = "_utt_ord"
    tmp = labeler.add_interlocutor_gender(tmp, order_col=order_col)
    return tmp


def fit(df: pd.DataFrame, outcomes: List[str], group_var: str) -> pd.DataFrame:
    rows = []
    # Reference levels
    df = df.copy()
    df["gender_match"] = df["gender_match"].astype(str)
    df["age_bucket"] = df["age_bucket"].astype(str)

    # For interpretable interactions, restrict to known categories.
    df = df[df["gender_match"].isin(["same", "different"])].copy()
    df = df[df["age_bucket"].ne("unknown")].copy()
    df["gender_match"] = pd.Categorical(df["gender_match"], ["same", "different"])

    # Choose most common non-unknown age bucket as reference (or first)
    age_counts = df["age_bucket"].value_counts()
    age_ref = str(age_counts.index[0]) if len(age_counts) else "Older"

    for y in outcomes:
        cols = [y, "gender_match", "age_bucket", "condition", group_var]
        has_dur = "duration_sec" in df.columns
        if has_dur:
            cols.append("duration_sec")
        d = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
        if len(d) < 500:
            rows.append({"feature": y, "success": False, "error": "insufficient_data"})
            continue

        rhs = [
            "C(gender_match, Treatment(reference='same')) * "
            f"C(age_bucket, Treatment(reference='{age_ref}'))",
            "C(condition)",
        ]
        if has_dur:
            rhs.append("duration_sec")
        formula = f"{_lhs(y)} ~ " + " + ".join(rhs)
        try:
            res = smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": d[group_var]})
        except Exception as e:
            rows.append({"feature": y, "success": False, "error": str(e)})
            continue

        # Collect key terms
        term_g = "C(gender_match, Treatment(reference='same'))[T.different]"
        base = {
            "feature": y,
            "success": True,
            "n_obs": len(d),
            "n_groups": int(d[group_var].nunique()),
            "age_ref": age_ref,
            "coef_diff_vs_same": float(res.params.get(term_g, np.nan)),
            "p_diff_vs_same": float(res.pvalues.get(term_g, np.nan)),
        }
        # Add per-age main effects and interactions
        for term, val in res.params.items():
            if "C(age_bucket" in term or ":" in term:
                base[f"coef::{term}"] = float(val)
        for term, p in res.pvalues.items():
            if "C(age_bucket" in term or ":" in term:
                base[f"p::{term}"] = float(p)
        rows.append(base)
    return pd.DataFrame(rows)


def main() -> None:
    p = argparse.ArgumentParser(description="Run interlocutor gender models with age_bucket interactions")
    p.add_argument("--input", type=str, required=True, help="Integrated features CSV")
    p.add_argument("--out-dir", type=str, required=True, help="Output directory")
    p.add_argument("--n-features", type=int, default=20)
    p.add_argument("--group-var", type=str, default="speaker")
    args = p.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    df = pd.read_csv(args.input, low_memory=False)
    labeled = add_labels(df, repo_root=repo_root)

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    outcomes = _select_numeric_features(labeled, int(args.n_features))
    models = fit(labeled, outcomes, group_var=str(args.group_var))
    models.to_csv(out_dir / "models_agebucket_interaction.csv", index=False)

    # Save label coverage summary
    labeled[["gender_match", "age_bucket"]].value_counts().rename("count").reset_index().to_csv(
        out_dir / "gender_match_x_age_bucket_counts.csv", index=False
    )
    print(f"Wrote {out_dir}")


if __name__ == "__main__":
    main()

