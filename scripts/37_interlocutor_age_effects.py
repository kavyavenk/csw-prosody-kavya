#!/usr/bin/env python3
"""
Interlocutor age effects on speaker prosody (exploratory).

Definitions (utterance-level):
- interlocutor = previous speaker within interaction (interaction_id, fallback file_id)
- interlocutor_age_bucket = age_bucket (mode) of the previous speaker within that interaction
- age_match ∈ {same, different, unknown}

Models (OLS with clustered SEs by speaker):
1) outcome ~ C(age_match) + C(condition) + C(gender) + C(age_bucket) [+ duration_sec]
2) outcome ~ C(interlocutor_age_bucket) + C(condition) + C(gender) + C(age_bucket) [+ duration_sec]
3) (optional combined) + C(gender_match) when available

Outputs:
- labels CSV
- per-outcome coefficient tables for age_match and interlocutor_age_bucket models
- short markdown report
"""

from __future__ import annotations

import argparse
import pathlib
from typing import List, Optional

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
    if "file_id" in df.columns:
        df[interaction_col] = df["file_id"].astype(str)
        return df
    raise ValueError(f"Cannot set {interaction_col}: missing file_id and column absent/empty")


def add_interlocutor_age(
    df: pd.DataFrame,
    interaction_col: str = "interaction_id",
    time_start_col: str = "start_time",
    time_end_col: str = "end_time",
    order_col: Optional[str] = None,
    speaker_col: str = "speaker",
    age_col: str = "age_bucket",
) -> pd.DataFrame:
    needed = {interaction_col, speaker_col, age_col}
    if order_col is None:
        needed |= {time_start_col, time_end_col}
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.copy()
    df = _ensure_interaction_id(df, interaction_col)
    df[speaker_col] = df[speaker_col].astype(str)
    df[age_col] = df[age_col].astype(str).replace({"nan": "unknown", "": "unknown"})

    # Sort within interaction to define "previous turn"
    if order_col is not None:
        df["_ord"] = pd.to_numeric(df[order_col], errors="coerce")
        df = df.sort_values([interaction_col, "_ord", "utt_id"], kind="mergesort")
    else:
        df["_start"] = pd.to_numeric(df[time_start_col], errors="coerce")
        df["_end"] = pd.to_numeric(df[time_end_col], errors="coerce")
        df = df.sort_values([interaction_col, "_start", "_end", "utt_id"], kind="mergesort")

    df["prev_speaker"] = df.groupby(interaction_col, dropna=False)[speaker_col].shift(1)

    # Speaker→age mapping (mode) per interaction
    spk_age = (
        df.groupby([interaction_col, speaker_col], dropna=False)[age_col]
        .apply(_safe_mode)
        .rename("speaker_age_mode")
        .reset_index()
    )
    df = df.merge(spk_age, on=[interaction_col, speaker_col], how="left", validate="m:1")
    df = df.merge(
        spk_age.rename(columns={speaker_col: "prev_speaker", "speaker_age_mode": "interlocutor_age_bucket"}),
        on=[interaction_col, "prev_speaker"],
        how="left",
        validate="m:1",
    )

    def match_row(r) -> str:
        a = str(r.get("speaker_age_mode") or "unknown")
        ia = str(r.get("interlocutor_age_bucket") or "unknown")
        if a == "unknown" or ia == "unknown":
            return "unknown"
        return "same" if a == ia else "different"

    df["age_match"] = df.apply(match_row, axis=1)

    drop_tmp = [c for c in ["_start", "_end", "_ord"] if c in df.columns]
    df = df.drop(columns=drop_tmp)
    return df


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


def _fit_age_match(df: pd.DataFrame, outcome: str, speaker_group: str) -> dict:
    cols = [outcome, "age_match", "condition", "gender", "age_bucket", speaker_group]
    if "duration_sec" in df.columns:
        cols.append("duration_sec")
    d = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) < 500:
        return {"feature": outcome, "success": False, "error": "insufficient_data"}

    d["age_match"] = pd.Categorical(d["age_match"].astype(str), ["same", "different", "unknown"])
    formula_terms = [
        "C(age_match, Treatment(reference='same'))",
        "C(condition)",
        "C(gender)",
        "C(age_bucket)",
    ]
    if "duration_sec" in d.columns:
        formula_terms.append("duration_sec")
    formula = f"{_lhs(outcome)} ~ " + " + ".join(formula_terms)

    res = smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": d[speaker_group]})
    key = "C(age_match, Treatment(reference='same'))[T.different]"
    return {
        "feature": outcome,
        "success": True,
        "n_obs": int(len(d)),
        "n_groups": int(d[speaker_group].nunique()),
        "coef_diff_vs_sameAge": float(res.params.get(key, np.nan)),
        "p_diff_vs_sameAge": float(res.pvalues.get(key, np.nan)),
    }


def _fit_interlocutor_age_bucket(df: pd.DataFrame, outcome: str, speaker_group: str) -> dict:
    cols = [outcome, "interlocutor_age_bucket", "condition", "gender", "age_bucket", speaker_group]
    if "duration_sec" in df.columns:
        cols.append("duration_sec")
    d = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) < 500:
        return {"feature": outcome, "success": False, "error": "insufficient_data"}

    # Use most frequent interlocutor bucket as reference to stabilize
    ref = str(d["interlocutor_age_bucket"].astype(str).value_counts().index[0])
    formula_terms = [
        f"C(interlocutor_age_bucket, Treatment(reference='{ref}'))",
        "C(condition)",
        "C(gender)",
        "C(age_bucket)",
    ]
    if "duration_sec" in d.columns:
        formula_terms.append("duration_sec")
    formula = f"{_lhs(outcome)} ~ " + " + ".join(formula_terms)
    res = smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": d[speaker_group]})

    # Collect any non-reference interlocutor_age terms
    out = {
        "feature": outcome,
        "success": True,
        "n_obs": int(len(d)),
        "n_groups": int(d[speaker_group].nunique()),
        "interlocutor_age_ref": ref,
    }
    for term, coef in res.params.items():
        if term.startswith("C(interlocutor_age_bucket"):
            out[f"coef::{term}"] = float(coef)
    for term, pv in res.pvalues.items():
        if term.startswith("C(interlocutor_age_bucket"):
            out[f"p::{term}"] = float(pv)
    return out


def run(input_csv: pathlib.Path, out_dir: pathlib.Path, n_features: int, speaker_group: str) -> None:
    df = pd.read_csv(input_csv, low_memory=False)
    if "utt_id" not in df.columns:
        raise ValueError("Expected utt_id column")
    for c in ["speaker", "gender", "age_bucket", "condition"]:
        if c not in df.columns:
            raise ValueError(f"Missing required column {c}")

    # Ordering inference (MASAC)
    order_col = None
    if "start_time" not in df.columns and "end_time" not in df.columns and "utt_id" in df.columns:
        parts = df["utt_id"].astype(str).str.rsplit("_", n=1, expand=True)
        if parts.shape[1] == 2:
            df["_utt_ord"] = pd.to_numeric(parts[1], errors="coerce")
            order_col = "_utt_ord"

    df = add_interlocutor_age(df, order_col=order_col)

    out_dir.mkdir(parents=True, exist_ok=True)
    # Save labels (full)
    label_cols = [
        "utt_id",
        "interaction_id" if "interaction_id" in df.columns else "file_id",
        "speaker",
        "speaker_age_mode",
        "prev_speaker",
        "interlocutor_age_bucket",
        "age_match",
        "gender",
        "age_bucket",
        "condition",
    ]
    label_cols = [c for c in label_cols if c in df.columns]
    df[label_cols].to_csv(out_dir / "interlocutor_age_labels.csv", index=False)

    outcomes = _select_numeric_features(df, n_features)
    # age_match models
    am_rows = [_fit_age_match(df, y, speaker_group=speaker_group) for y in outcomes]
    pd.DataFrame(am_rows).to_csv(out_dir / "age_match_models.csv", index=False)
    # interlocutor age bucket models
    ia_rows = [_fit_interlocutor_age_bucket(df, y, speaker_group=speaker_group) for y in outcomes]
    pd.DataFrame(ia_rows).to_csv(out_dir / "interlocutor_age_bucket_models.csv", index=False)

    # Quick markdown report
    rep = []
    rep.append("# Interlocutor age effects (exploratory)")
    rep.append("")
    rep.append(f"- Input: `{input_csv}`")
    rep.append(f"- Rows: {len(df):,}")
    rep.append(f"- Outcomes modeled (top variance, n={len(outcomes)}): {', '.join(outcomes)}")
    rep.append("")
    rep.append("## Labels")
    rep.append(f"- Wrote: `{out_dir / 'interlocutor_age_labels.csv'}`")
    rep.append("")
    rep.append("## Models")
    rep.append(f"- Age-match models: `{out_dir / 'age_match_models.csv'}` (different-age vs same-age)")
    rep.append(f"- Interlocutor-age-bucket models: `{out_dir / 'interlocutor_age_bucket_models.csv'}`")
    rep.append("")
    rep.append("## Notes")
    rep.append("- Interlocutor is operationalized as the **previous speaker turn** within an interaction.")
    rep.append("- These models control for speaker’s own age_bucket, gender, and condition (and duration if present).")
    (out_dir / "interlocutor_age_report.md").write_text("\n".join(rep), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Interlocutor age effects on prosody")
    p.add_argument("--input", type=str, required=True)
    p.add_argument("--out-dir", type=str, required=True)
    p.add_argument("--n-features", type=int, default=30)
    p.add_argument("--speaker-group", type=str, default="speaker")
    args = p.parse_args()

    run(
        input_csv=pathlib.Path(args.input),
        out_dir=pathlib.Path(args.out_dir),
        n_features=int(args.n_features),
        speaker_group=str(args.speaker_group),
    )

