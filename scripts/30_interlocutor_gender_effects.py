#!/usr/bin/env python3
"""
Explore how interlocutor gender (same vs different) relates to speaker prosody.

Operationalization (utterance-level):
- Within each interaction (default: file_id), define the interlocutor as the *previous* speaker
  in time (sorted by start_time/end_time).
- interlocutor_gender = gender of previous speaker (mode within interaction×speaker).
- gender_match ∈ {same, different, unknown}

Outputs:
- A compact CSV of model coefficients for gender_match across selected prosodic features
- A markdown report with toplines + modeling notes

This is intentionally exploratory (not a confirmatory preregistered analysis).
"""

from __future__ import annotations

import argparse
import pathlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def _safe_mode(series: pd.Series) -> Optional[str]:
    s = series.dropna().astype(str)
    if s.empty:
        return None
    vc = s.value_counts()
    if vc.empty:
        return None
    return str(vc.index[0])


def _ensure_interaction_id(df: pd.DataFrame, interaction_col: str) -> pd.DataFrame:
    if interaction_col in df.columns and df[interaction_col].notna().any():
        return df
    # Fallback: for this repo, SEAME "interaction" is best approximated by file_id.
    if "file_id" in df.columns:
        df[interaction_col] = df["file_id"].astype(str)
        return df
    raise ValueError(f"Cannot set {interaction_col}: missing file_id and column absent/empty")


def add_interlocutor_gender(
    df: pd.DataFrame,
    interaction_col: str = "interaction_id",
    time_start_col: str = "start_time",
    time_end_col: str = "end_time",
    order_col: Optional[str] = None,
    speaker_col: str = "speaker",
    gender_col: str = "gender",
) -> pd.DataFrame:
    """
    Add:
      - prev_speaker
      - interlocutor_gender
      - gender_match
    """
    needed = {interaction_col, speaker_col, gender_col}
    if order_col is None:
        needed |= {time_start_col, time_end_col}
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.copy()
    df = _ensure_interaction_id(df, interaction_col)

    # Normalize types
    df[speaker_col] = df[speaker_col].astype(str)
    df[gender_col] = df[gender_col].astype(str).str.lower().replace({"nan": "unknown", "": "unknown"})

    # Sort within interaction to define "previous turn"
    if order_col is not None:
        df["_ord"] = pd.to_numeric(df[order_col], errors="coerce")
        df = df.sort_values([interaction_col, "_ord", "utt_id"], kind="mergesort")
    else:
        df["_start"] = pd.to_numeric(df[time_start_col], errors="coerce")
        df["_end"] = pd.to_numeric(df[time_end_col], errors="coerce")
        df = df.sort_values([interaction_col, "_start", "_end", "utt_id"], kind="mergesort")

    # Previous speaker per interaction
    df["prev_speaker"] = df.groupby(interaction_col, dropna=False)[speaker_col].shift(1)

    # Speaker→gender mapping (mode) per interaction (guards against any row-level inconsistencies)
    spk_gender = (
        df.groupby([interaction_col, speaker_col], dropna=False)[gender_col]
        .apply(_safe_mode)
        .rename("speaker_gender_mode")
        .reset_index()
    )
    df = df.merge(
        spk_gender,
        on=[interaction_col, speaker_col],
        how="left",
        validate="m:1",
    )
    df = df.merge(
        spk_gender.rename(columns={speaker_col: "prev_speaker", "speaker_gender_mode": "interlocutor_gender"}),
        on=[interaction_col, "prev_speaker"],
        how="left",
        validate="m:1",
    )

    # Compute match
    def match_row(r) -> str:
        g = str(r.get("speaker_gender_mode") or "unknown").lower()
        ig = str(r.get("interlocutor_gender") or "unknown").lower()
        if g not in ("male", "female") or ig not in ("male", "female"):
            return "unknown"
        return "same" if g == ig else "different"

    df["gender_match"] = df.apply(match_row, axis=1)

    # Clean up
    drop_tmp = [c for c in ["_start", "_end", "_ord"] if c in df.columns]
    df = df.drop(columns=drop_tmp)
    return df


def _select_numeric_features(df: pd.DataFrame, n: int) -> List[str]:
    # Exclude obvious metadata-like numeric columns
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


def _outcome_lhs(col: str) -> str:
    # Patsy requires quoting for names like "1F0mean"
    if col.isidentifier():
        return col
    esc = str(col).replace("\\", "\\\\").replace('"', '\\"')
    return f'Q("{esc}")'


@dataclass(frozen=True)
class ModelRow:
    feature: str
    n_obs: int
    group_var: str
    n_groups: int
    coef_diff_vs_same: float
    p_diff_vs_same: float
    coef_unknown_vs_same: float
    p_unknown_vs_same: float


def _fit_one(
    df: pd.DataFrame,
    feature: str,
    group_var: str,
    predictors: List[str],
) -> Tuple[Optional[ModelRow], Optional[str], Optional[str]]:
    cols = [feature, group_var] + predictors
    model_df = df[cols].copy()
    model_df = model_df.replace([np.inf, -np.inf], np.nan).dropna()
    if len(model_df) < 200:
        return None, "insufficient_data", None

    # Ensure categorical encoding for gender_match
    if "gender_match" in predictors:
        model_df["gender_match"] = pd.Categorical(
            model_df["gender_match"].astype(str),
            categories=["same", "different", "unknown"],
            ordered=False,
        )

    fixed_terms = []
    for p in predictors:
        if p == "gender_match":
            fixed_terms.append("C(gender_match, Treatment(reference='same'))")
        elif model_df[p].dtype == "object" or model_df[p].dtype.name == "category":
            fixed_terms.append(f"C({p})")
        else:
            fixed_terms.append(p)

    formula = f"{_outcome_lhs(feature)} ~ " + " + ".join(fixed_terms)

    try:
        model = smf.mixedlm(formula, model_df, groups=model_df[group_var])
        res = model.fit(method=["lbfgs", "powell"])
    except Exception as e:
        # fallback attempt: different optimizer
        try:
            model = smf.mixedlm(formula, model_df, groups=model_df[group_var])
            res = model.fit(method="lbfgs")
        except Exception as e2:
            # final fallback: OLS with cluster-robust SEs by group_var
            try:
                ols = smf.ols(formula, model_df).fit(
                    cov_type="cluster", cov_kwds={"groups": model_df[group_var]}
                )
                res = ols
            except Exception as e3:
                return None, "fit_failed", f"{e2}; OLS fallback failed: {e3}"

    params = res.params.to_dict()
    pvals = res.pvalues.to_dict()

    # Statsmodels names these coefficients like:
    # C(gender_match, Treatment(reference='same'))[T.different]
    key_diff = "C(gender_match, Treatment(reference='same'))[T.different]"
    key_unk = "C(gender_match, Treatment(reference='same'))[T.unknown]"
    row = ModelRow(
        feature=feature,
        n_obs=len(model_df),
        group_var=group_var,
        n_groups=int(model_df[group_var].nunique()),
        coef_diff_vs_same=float(params.get(key_diff, np.nan)),
        p_diff_vs_same=float(pvals.get(key_diff, np.nan)),
        coef_unknown_vs_same=float(params.get(key_unk, np.nan)),
        p_unknown_vs_same=float(pvals.get(key_unk, np.nan)),
    )
    return row, None, str(res.summary())


def run(
    input_csv: pathlib.Path,
    output_dir: pathlib.Path,
    n_features: int,
    group_var: str,
    include_controls: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv, low_memory=False)
    if "utt_id" not in df.columns:
        raise ValueError("Expected utt_id column in input CSV")

    # MASAC doesn't have start_time/end_time in the integrated table; infer ordering from utt_id suffix when present.
    order_col = None
    if "start_time" not in df.columns and "end_time" not in df.columns and "utt_id" in df.columns:
        # If utt_id like train_337_0 → order=0
        parts = df["utt_id"].astype(str).str.rsplit("_", n=1, expand=True)
        if parts.shape[1] == 2:
            df["_utt_ord"] = pd.to_numeric(parts[1], errors="coerce")
            order_col = "_utt_ord"

    df = add_interlocutor_gender(df, order_col=order_col)

    # Modeling subset: only utterances with a previous speaker
    df_model = df[df["prev_speaker"].notna()].copy()

    # Predictors
    predictors = ["gender_match"]
    if include_controls:
        # Avoid collinearity: condition already encodes CS vs mono language state.
        for col in ["condition", "duration_sec"]:
            if col in df_model.columns and df_model[col].nunique(dropna=True) > 1:
                predictors.append(col)

    if group_var not in df_model.columns:
        if group_var == "interaction_id" and "file_id" in df_model.columns:
            df_model[group_var] = df_model["file_id"].astype(str)
        else:
            raise ValueError(f"group_var not found in data: {group_var}")

    # Select outcomes
    features = _select_numeric_features(df_model, n_features)
    if not features:
        raise ValueError("No numeric features found to model")

    rows: List[Dict[str, object]] = []
    summaries: List[Tuple[str, str]] = []
    for feat in features:
        row, err, summary = _fit_one(df_model, feat, group_var, predictors)
        if row is None:
            rows.append({"feature": feat, "success": False, "error": err})
            continue
        rows.append(
            {
                "feature": row.feature,
                "success": True,
                "n_obs": row.n_obs,
                "group_var": row.group_var,
                "n_groups": row.n_groups,
                "coef_diff_vs_same": row.coef_diff_vs_same,
                "p_diff_vs_same": row.p_diff_vs_same,
                "coef_unknown_vs_same": row.coef_unknown_vs_same,
                "p_unknown_vs_same": row.p_unknown_vs_same,
            }
        )
        if summary:
            summaries.append((feat, summary))

    out_csv = output_dir / "seame_interlocutor_gender_models.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)

    # Write a short markdown report
    report = []
    report.append("# SEAME: Interlocutor gender and prosody (exploratory)")
    report.append("")
    report.append(f"- Input: `{input_csv}`")
    report.append(f"- Rows (all): {len(df):,}")
    report.append(f"- Rows with defined interlocutor (prev_speaker): {len(df_model):,}")
    report.append(f"- Grouping (random intercept): `{group_var}` (n={df_model[group_var].nunique():,})")
    report.append(f"- Outcomes modeled (top variance, n={len(features)}): {', '.join(features)}")
    report.append(f"- Predictors: {', '.join(predictors)}")
    report.append("")
    report.append("## Key coefficient")
    report.append(
        "Each model includes `gender_match` with **same-gender as reference**; "
        "`coef_diff_vs_same` is the estimated mean difference in the outcome for mixed-gender vs same-gender turns."
    )
    report.append("")
    report.append(f"- Results table: `{out_csv}`")
    report.append("")
    report.append("## Notes / caveats")
    report.append("- Interlocutor is defined as the previous speaker in the same `file_id` interaction.")
    report.append("- This does not distinguish addressee vs overhearer; it’s turn-adjacent by construction.")
    report.append("- Interaction-level IDs were missing in the integrated file; we fall back to `file_id`.")
    report.append("")

    # Include up to 3 full model summaries for inspection (most significant if any)
    res_df = pd.DataFrame(rows)
    if "success" in res_df.columns and "p_diff_vs_same" in res_df.columns:
        sig = res_df[(res_df["success"] == True) & (res_df["p_diff_vs_same"].notna())].copy()
        sig = sig.sort_values("p_diff_vs_same", ascending=True).head(3)
        if not sig.empty:
            report.append("## Example model summaries (lowest p-values)")
            for feat in sig["feature"].tolist():
                s = dict(summaries).get(feat)
                if not s:
                    continue
                report.append(f"### {feat}")
                report.append("```")
                report.append(s)
                report.append("```")

    out_md = output_dir / "seame_interlocutor_gender_report.md"
    out_md.write_text("\n".join(report), encoding="utf-8")

    # Save derived metadata (full rows) for reproducibility
    meta_cols = [
        "utt_id",
        "file_id",
        "speaker",
        "speaker_gender_mode",
        "prev_speaker",
        "interlocutor_gender",
        "gender_match",
        "start_time",
        "end_time",
        "lang",
        "condition",
    ]
    meta_cols = [c for c in meta_cols if c in df.columns]
    df[meta_cols].to_csv(output_dir / "seame_interlocutor_gender_labels.csv", index=False)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Explore interlocutor gender effects on prosody (SEAME)")
    p.add_argument(
        "--input",
        type=str,
        default="results/functional_anchors/seame/seame_integrated_features.csv",
        help="Integrated SEAME features CSV (with speaker gender)",
    )
    p.add_argument(
        "--output-dir",
        type=str,
        default="results/interlocutor_gender/seame",
        help="Output directory",
    )
    p.add_argument("--n-features", type=int, default=12, help="Number of outcomes to model")
    p.add_argument(
        "--group-var",
        type=str,
        default="file_id",
        help="Grouping variable for random intercept (e.g., speaker or file_id)",
    )
    p.add_argument(
        "--no-controls",
        action="store_true",
        help="If set, exclude basic controls (condition/lang/duration_sec) from fixed effects",
    )
    args = p.parse_args()

    run(
        input_csv=pathlib.Path(args.input),
        output_dir=pathlib.Path(args.output_dir),
        n_features=int(args.n_features),
        group_var=str(args.group_var),
        include_controls=not bool(args.no_controls),
    )

