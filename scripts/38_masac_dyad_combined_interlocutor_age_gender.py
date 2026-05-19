#!/usr/bin/env python3
"""
MASAC dyad-only combined interlocutor model: age + gender together.

We merge:
- dyad subset integrated features
- interlocutor gender labels (gender_match) from `results/interlocutor_gender/masac_dyad/models/seame_interlocutor_gender_labels.csv`
- interlocutor age labels (interlocutor_age_bucket, age_match) from `results/interlocutor_age/masac_dyad/interlocutor_age_labels.csv`

Then fit OLS with clustered SEs by speaker:
Additive model:
  outcome ~ C(gender_match) + C(interlocutor_age_bucket) + controls

Interaction model (optional):
  outcome ~ C(gender_match) * C(interlocutor_age_bucket) + controls

Controls:
  C(condition) + C(gender) + C(age_bucket) [+ duration_sec if present]

Outputs:
- combined_design.csv (minimal columns used)
- additive_models.csv (key coefs/pvals)
- interaction_models.csv (key interaction pvals)
- FDR-adjusted versions for key terms
"""

from __future__ import annotations

import argparse
import pathlib
from typing import Dict, List, Tuple

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


def _fdr_add(df: pd.DataFrame, p_col: str, out_col: str) -> pd.DataFrame:
    out = df.copy()
    p = pd.to_numeric(out[p_col], errors="coerce")
    mask = ~p.isna()
    if mask.sum() == 0:
        out[out_col] = np.nan
        return out
    _, padj, _, _ = multipletests(p[mask].values, method="fdr_bh")
    out.loc[mask, out_col] = padj
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="MASAC dyad combined interlocutor age+gender models")
    p.add_argument(
        "--dyad",
        type=str,
        default="results/interlocutor_gender/masac_dyad/masac_integrated_features_dyad.csv",
        help="Dyad-only integrated features CSV",
    )
    p.add_argument(
        "--gender-labels",
        type=str,
        default="results/interlocutor_gender/masac_dyad/models/seame_interlocutor_gender_labels.csv",
        help="Interlocutor gender labels CSV",
    )
    p.add_argument(
        "--age-labels",
        type=str,
        default="results/interlocutor_age/masac_dyad/interlocutor_age_labels.csv",
        help="Interlocutor age labels CSV",
    )
    p.add_argument("--out-dir", type=str, default="results/interlocutor_combined/masac_dyad")
    p.add_argument("--n-features", type=int, default=30)
    args = p.parse_args()

    dyad = pd.read_csv(args.dyad, low_memory=False)
    g = pd.read_csv(args.gender_labels, low_memory=False)[["utt_id", "gender_match"]]
    a = pd.read_csv(args.age_labels, low_memory=False)[["utt_id", "interlocutor_age_bucket", "age_match"]]

    df = dyad.merge(g, on="utt_id", how="left").merge(a, on="utt_id", how="left")
    df["gender_match"] = df["gender_match"].fillna("unknown").astype(str)
    df["interlocutor_age_bucket"] = df["interlocutor_age_bucket"].fillna("unknown").astype(str)

    # Keep interpretable categories only
    df = df[df["gender_match"].isin(["same", "different"])].copy()
    df = df[df["interlocutor_age_bucket"].isin(["Younger", "Older"])].copy()

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Minimal design snapshot
    keep_cols = [
        "utt_id",
        "speaker",
        "condition",
        "gender",
        "age_bucket",
        "gender_match",
        "interlocutor_age_bucket",
    ]
    if "duration_sec" in df.columns:
        keep_cols.append("duration_sec")
    df[keep_cols].to_csv(out_dir / "combined_design.csv", index=False)

    outcomes = _select_numeric_features(df, int(args.n_features))
    rows_add = []
    rows_int = []

    for y in outcomes:
        base_cols = [y, "speaker", "condition", "gender", "age_bucket", "gender_match", "interlocutor_age_bucket"]
        if "duration_sec" in df.columns:
            base_cols.append("duration_sec")
        d = df[base_cols].replace([np.inf, -np.inf], np.nan).dropna()
        if len(d) < 500:
            continue

        d["gender_match"] = pd.Categorical(d["gender_match"], ["same", "different"])
        d["interlocutor_age_bucket"] = pd.Categorical(d["interlocutor_age_bucket"], ["Younger", "Older"])

        controls = ["C(condition)", "C(gender)", "C(age_bucket)"]
        if "duration_sec" in d.columns:
            controls.append("duration_sec")

        # Additive
        f_add = (
            f"{_lhs(y)} ~ "
            "C(gender_match, Treatment(reference='same')) + "
            "C(interlocutor_age_bucket, Treatment(reference='Younger')) + "
            + " + ".join(controls)
        )
        res_add = smf.ols(f_add, d).fit(cov_type="cluster", cov_kwds={"groups": d["speaker"]})
        key_g = "C(gender_match, Treatment(reference='same'))[T.different]"
        key_a = "C(interlocutor_age_bucket, Treatment(reference='Younger'))[T.Older]"
        rows_add.append(
            {
                "feature": y,
                "n_obs": int(len(d)),
                "n_speakers": int(d["speaker"].nunique()),
                "coef_gender_diff_vs_same": float(res_add.params.get(key_g, np.nan)),
                "p_gender_diff_vs_same": float(res_add.pvalues.get(key_g, np.nan)),
                "coef_interlocutorOlder_vs_Younger": float(res_add.params.get(key_a, np.nan)),
                "p_interlocutorOlder_vs_Younger": float(res_add.pvalues.get(key_a, np.nan)),
            }
        )

        # Interaction
        f_int = (
            f"{_lhs(y)} ~ "
            "C(gender_match, Treatment(reference='same')) * "
            "C(interlocutor_age_bucket, Treatment(reference='Younger')) + "
            + " + ".join(controls)
        )
        res_int = smf.ols(f_int, d).fit(cov_type="cluster", cov_kwds={"groups": d["speaker"]})
        key_int = (
            "C(gender_match, Treatment(reference='same'))[T.different]:"
            "C(interlocutor_age_bucket, Treatment(reference='Younger'))[T.Older]"
        )
        rows_int.append(
            {
                "feature": y,
                "n_obs": int(len(d)),
                "n_speakers": int(d["speaker"].nunique()),
                "coef_interaction": float(res_int.params.get(key_int, np.nan)),
                "p_interaction": float(res_int.pvalues.get(key_int, np.nan)),
            }
        )

    add_df = pd.DataFrame(rows_add)
    int_df = pd.DataFrame(rows_int)

    add_df.to_csv(out_dir / "additive_models.csv", index=False)
    int_df.to_csv(out_dir / "interaction_models.csv", index=False)

    # FDR for key tests
    add_df_fdr = _fdr_add(add_df, "p_gender_diff_vs_same", "p_adj_fdr_gender")
    add_df_fdr = _fdr_add(add_df_fdr, "p_interlocutorOlder_vs_Younger", "p_adj_fdr_interlocutor_age")
    add_df_fdr.to_csv(out_dir / "additive_models_fdr.csv", index=False)

    int_df_fdr = _fdr_add(int_df, "p_interaction", "p_adj_fdr_interaction")
    int_df_fdr.to_csv(out_dir / "interaction_models_fdr.csv", index=False)

    # Short markdown
    rep = []
    rep.append("# MASAC dyad: combined interlocutor age + gender")
    rep.append("")
    rep.append(f"- Dyad rows used (after dropping unknown categories): {len(df):,}")
    rep.append(f"- Outcomes modeled: {len(add_df):,}")
    rep.append("")
    rep.append("## Additive model (gender + age together)")
    sig_g = (add_df_fdr["p_adj_fdr_gender"] < 0.05).sum() if len(add_df_fdr) else 0
    sig_a = (add_df_fdr["p_adj_fdr_interlocutor_age"] < 0.05).sum() if len(add_df_fdr) else 0
    rep.append(f"- Significant (FDR<0.05) gender-diff-vs-same terms: **{int(sig_g)}**")
    rep.append(f"- Significant (FDR<0.05) interlocutor-Older-vs-Younger terms: **{int(sig_a)}**")
    rep.append("")
    rep.append("## Interaction model (gender × interlocutor age)")
    sig_i = (int_df_fdr["p_adj_fdr_interaction"] < 0.05).sum() if len(int_df_fdr) else 0
    rep.append(f"- Significant (FDR<0.05) interaction terms: **{int(sig_i)}**")
    rep.append("")
    rep.append("Files:")
    rep.append(f"- `{out_dir / 'additive_models_fdr.csv'}`")
    rep.append(f"- `{out_dir / 'interaction_models_fdr.csv'}`")
    rep.append(f"- `{out_dir / 'combined_design.csv'}`")
    (out_dir / "combined_report.md").write_text("\n".join(rep), encoding="utf-8")


if __name__ == "__main__":
    main()

