#!/usr/bin/env python3
"""
Build cross-corpus comparison tables from directionality OLS outputs (MASAC vs SEAME).

Reads:
  results/directionality_models/{corpus}/{corpus}_condition_models_ols.csv
  results/directionality_models/{corpus}/{corpus}_cs_directionality_models_ols.csv

Writes:
  results/cross_corpus/directionality_comparison_summary.md
  results/cross_corpus/directionality_comparison_features.csv
"""

import argparse
import ast
import pathlib
from typing import Any, Dict, Optional

import pandas as pd


def _parse_dict_cell(val: Any) -> Optional[Dict]:
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, dict):
        return val
    s = str(val).strip()
    if not s:
        return None
    try:
        return ast.literal_eval(s)
    except Exception:
        return None


def flatten_models(csv_path: pathlib.Path, corpus: str, model_type: str) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(csv_path, low_memory=False)
    rows = []
    for _, r in df.iterrows():
        feat = r.get("feature")
        params = _parse_dict_cell(r.get("params"))
        pvals = _parse_dict_cell(r.get("pvalues"))
        if not params:
            continue
        for term, coef in params.items():
            rows.append(
                {
                    "corpus": corpus,
                    "model_type": model_type,
                    "feature": feat,
                    "term": term,
                    "coef": coef,
                    "p_value": pvals.get(term) if pvals else None,
                    "aic": r.get("aic"),
                    "n": r.get("n"),
                }
            )
    return pd.DataFrame(rows)


def run_comparison(
    masac_dir: pathlib.Path,
    seame_dir: pathlib.Path,
    out_dir: pathlib.Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    pieces = []
    for corpus, base in [("masac", masac_dir), ("seame", seame_dir)]:
        cond = base / f"{corpus}_condition_models_ols.csv"
        cs = base / f"{corpus}_cs_directionality_models_ols.csv"
        pieces.append(flatten_models(cond, corpus, "all_condition"))
        pieces.append(flatten_models(cs, corpus, "cs_directionality"))

    long = pd.concat([p for p in pieces if not p.empty], ignore_index=True)
    if long.empty:
        print("No model rows found; run scripts/25_run_directionality_models.py for each corpus.")
        return

    long.to_csv(out_dir / "directionality_comparison_long.csv", index=False)

    # Wide: same feature + term across corpora
    pivot = long.pivot_table(
        index=["model_type", "feature", "term"],
        columns="corpus",
        values="coef",
        aggfunc="first",
    )
    pivot_p = long.pivot_table(
        index=["model_type", "feature", "term"],
        columns="corpus",
        values="p_value",
        aggfunc="first",
    )
    pivot.to_csv(out_dir / "directionality_coef_pivot.csv")
    pivot_p.to_csv(out_dir / "directionality_pvalue_pivot.csv")

    lines = [
        "# Cross-corpus directionality / condition model comparison",
        "",
        "Coefficients are from OLS models (script 25). Interpret with caution; mixed-effects versions on SEAME/MASAC with speaker RE are in scripts 18/23.",
        "",
        "## Rows: model_type × feature × term",
        "",
        "See `directionality_comparison_long.csv` for full table.",
        "",
        "### MASAC vs SEAME coefficient pivot (same feature/term)",
        "",
        pivot.head(40).to_string(),
        "",
    ]
    (out_dir / "directionality_comparison_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote comparison under {out_dir}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Cross-corpus comparison of directionality OLS outputs")
    p.add_argument(
        "--masac-dir",
        type=str,
        default="results/directionality_models/masac",
        help="Directory with masac_*_ols.csv",
    )
    p.add_argument(
        "--seame-dir",
        type=str,
        default="results/directionality_models/seame",
        help="Directory with seame_*_ols.csv",
    )
    p.add_argument(
        "--output-dir",
        type=str,
        default="results/cross_corpus",
        help="Output directory",
    )
    args = p.parse_args()
    run_comparison(pathlib.Path(args.masac_dir), pathlib.Path(args.seame_dir), pathlib.Path(args.output_dir))
