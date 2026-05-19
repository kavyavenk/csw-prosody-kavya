#!/usr/bin/env python3
"""
SEAME: nationality and prosody.

Background
----------
Turn-adjacent "interlocutor nationality" (same vs different nationality as the
previous speaker) is often **not identifiable** in this corpus: within each
recording (`file_id`), all labeled speakers share one nationality label, so the
previous speaker is always same-nationality by construction.

We therefore report (1) diagnostics for that interlocutor operationalization and
(2) **speaker-level nationality** effects (Malaysian vs Singaporean), which is
the identifiable quantity in the current labels and answers the closely related
question of whether community/nationality co-varies with prosody profiles.
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


def add_interlocutor_nationality_match(
    df: pd.DataFrame,
    interaction_col: str = "file_id",
    time_start_col: str = "start_time",
    time_end_col: str = "end_time",
    order_col: Optional[str] = None,
    speaker_col: str = "speaker",
    nationality_col: str = "nationality",
) -> pd.DataFrame:
    """Add prev_speaker, interlocutor_nationality, nationality_match (same/different/unknown)."""
    needed = {interaction_col, speaker_col, nationality_col}
    if order_col is None:
        needed |= {time_start_col, time_end_col}
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = df.copy()
    out[speaker_col] = out[speaker_col].astype(str)
    out[nationality_col] = (
        out[nationality_col].astype(str).str.lower().replace({"nan": "unknown", "": "unknown"})
    )

    if order_col is not None:
        out["_ord"] = pd.to_numeric(out[order_col], errors="coerce")
        out = out.sort_values([interaction_col, "_ord", "utt_id"], kind="mergesort")
    else:
        out["_start"] = pd.to_numeric(out[time_start_col], errors="coerce")
        out["_end"] = pd.to_numeric(out[time_end_col], errors="coerce")
        out = out.sort_values([interaction_col, "_start", "_end", "utt_id"], kind="mergesort")

    out["prev_speaker"] = out.groupby(interaction_col, dropna=False)[speaker_col].shift(1)

    spk_nat = (
        out.groupby([interaction_col, speaker_col], dropna=False)[nationality_col]
        .apply(_safe_mode)
        .rename("speaker_nationality_mode")
        .reset_index()
    )
    out = out.merge(spk_nat, on=[interaction_col, speaker_col], how="left", validate="m:1")
    out = out.merge(
        spk_nat.rename(
            columns={speaker_col: "prev_speaker", "speaker_nationality_mode": "interlocutor_nationality"}
        ),
        on=[interaction_col, "prev_speaker"],
        how="left",
        validate="m:1",
    )

    def match_row(r) -> str:
        a = str(r.get("speaker_nationality_mode") or "unknown").lower()
        b = str(r.get("interlocutor_nationality") or "unknown").lower()
        if a == "unknown" or b == "unknown":
            return "unknown"
        return "same" if a == b else "different"

    out["nationality_match"] = out.apply(match_row, axis=1)
    drop_tmp = [c for c in ["_start", "_end", "_ord"] if c in out.columns]
    out = out.drop(columns=drop_tmp)
    return out


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


def _outcome_lhs(col: str) -> str:
    if col.isidentifier():
        return col
    esc = str(col).replace("\\", "\\\\").replace('"', '\\"')
    return f'Q("{esc}")'


@dataclass(frozen=True)
class SpeakerNatRow:
    feature: str
    n_obs: int
    n_groups: int
    coef_malaysian_vs_singaporean: float
    p_malaysian_vs_singaporean: float


def _fit_speaker_nationality_mixedlm(
    df: pd.DataFrame,
    feature: str,
    group_var: str,
    predictors: List[str],
) -> Tuple[Optional[SpeakerNatRow], Optional[str], Optional[str]]:
    cols = [feature, group_var] + predictors
    model_df = df[cols].copy()
    model_df = model_df.replace([np.inf, -np.inf], np.nan).dropna()
    if len(model_df) < 200:
        return None, "insufficient_data", None

    if "nationality" in predictors:
        model_df["nationality"] = pd.Categorical(
            model_df["nationality"].astype(str).str.lower(),
            categories=["singaporean", "malaysian"],
            ordered=False,
        )

    fixed_terms = []
    for p in predictors:
        if p == "nationality":
            fixed_terms.append("C(nationality, Treatment(reference='singaporean'))")
        elif p == "condition":
            fixed_terms.append("C(condition)")
        elif model_df[p].dtype == "object" or model_df[p].dtype.name == "category":
            fixed_terms.append(f"C({p})")
        else:
            fixed_terms.append(p)

    formula = f"{_outcome_lhs(feature)} ~ " + " + ".join(fixed_terms)

    try:
        model = smf.mixedlm(formula, model_df, groups=model_df[group_var])
        res = model.fit(method=["lbfgs", "powell"])
    except Exception:
        try:
            model = smf.mixedlm(formula, model_df, groups=model_df[group_var])
            res = model.fit(method="lbfgs")
        except Exception as e2:
            return None, f"fit_failed: {e2}", None

    params = res.params.to_dict()
    pvals = res.pvalues.to_dict()
    key = "C(nationality, Treatment(reference='singaporean'))[T.malaysian]"
    row = SpeakerNatRow(
        feature=feature,
        n_obs=len(model_df),
        n_groups=int(model_df[group_var].nunique()),
        coef_malaysian_vs_singaporean=float(params.get(key, np.nan)),
        p_malaysian_vs_singaporean=float(pvals.get(key, np.nan)),
    )
    return row, None, str(res.summary())


def run(
    input_csv: pathlib.Path,
    output_dir: pathlib.Path,
    n_features: int,
    group_var: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv, low_memory=False)
    if "utt_id" not in df.columns:
        raise ValueError("Expected utt_id column in input CSV")

    order_col = None
    if "start_time" not in df.columns and "end_time" not in df.columns and "utt_id" in df.columns:
        parts = df["utt_id"].astype(str).str.rsplit("_", n=1, expand=True)
        if parts.shape[1] == 2:
            df["_utt_ord"] = pd.to_numeric(parts[1], errors="coerce")
            order_col = "_utt_ord"

    df_diag = add_interlocutor_nationality_match(df, order_col=order_col)
    sub_prev = df_diag[df_diag["prev_speaker"].notna()].copy()
    vc = sub_prev["nationality_match"].value_counts()
    diag_lines = [
        "# SEAME interlocutor-nationality diagnostics (turn-adjacent within `file_id`)",
        "",
        f"- Total rows: {len(df):,}",
        f"- Rows with previous speaker (same file): {len(sub_prev):,}",
        f"- `nationality_match` counts: {vc.to_dict()}",
        "",
        "If `different` is zero, the corpus does not realize cross-nationality ",
        "turn adjacency within recordings; interpret the modeling below as **speaker nationality**.",
        "",
    ]
    (output_dir / "interlocutor_nationality_diagnostics.md").write_text("\n".join(diag_lines), encoding="utf-8")

    meta_cols = [
        "utt_id",
        "file_id",
        "speaker",
        "speaker_nationality_mode",
        "prev_speaker",
        "interlocutor_nationality",
        "nationality_match",
        "condition",
    ]
    meta_cols = [c for c in meta_cols if c in df_diag.columns]
    df_diag[meta_cols].to_csv(output_dir / "seame_interlocutor_nationality_labels.csv", index=False)

    # Speaker-nationality models (identifiable contrast)
    df["nationality"] = df["nationality"].astype(str).str.lower()
    df_model = df[df["nationality"].isin(["singaporean", "malaysian"])].copy()

    predictors: List[str] = ["nationality"]
    for col in ["condition", "has_discourse_marker", "has_repetition", "duration_sec"]:
        if col in df_model.columns and df_model[col].nunique(dropna=True) > 1:
            predictors.append(col)

    if group_var not in df_model.columns:
        raise ValueError(f"group_var not found: {group_var}")

    features = _select_numeric_features(df_model, n_features)
    if not features:
        raise ValueError("No numeric features found to model")

    rows: List[Dict[str, object]] = []
    summaries: List[Tuple[str, str]] = []
    for feat in features:
        row, err, summary = _fit_speaker_nationality_mixedlm(df_model, feat, group_var, predictors)
        if row is None:
            rows.append({"feature": feat, "success": False, "error": err})
            continue
        rows.append(
            {
                "feature": row.feature,
                "success": True,
                "n_obs": row.n_obs,
                "n_groups": row.n_groups,
                "coef_malaysian_vs_singaporean": row.coef_malaysian_vs_singaporean,
                "p_malaysian_vs_singaporean": row.p_malaysian_vs_singaporean,
            }
        )
        if summary:
            summaries.append((feat, summary))

    out_csv = output_dir / "seame_speaker_nationality_mixedlm.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)

    report: List[str] = []
    report.append("# SEAME: Nationality and prosody")
    report.append("")
    report.append(f"- Input: `{input_csv}`")
    report.append(f"- Interlocutor diagnostics: `{output_dir / 'interlocutor_nationality_diagnostics.md'}`")
    report.append(f"- Speaker-nationality models (Malaysian vs Singaporean reference): `{out_csv}`")
    report.append("")
    report.append("## Speaker-level mixed-effects models")
    report.append(
        f"- Formula family: `outcome ~ C(nationality) + controls`, controls={predictors[1:]}, "
        f"random intercept: `{group_var}`."
    )
    report.append(f"- Rows after restricting nationality ∈ {{malaysian, singaporean}}: {len(df_model):,}")
    report.append(f"- Outcomes (top variance, n={len(features)}): {', '.join(features)}")
    report.append("")
    report.append(
        "Coefficient **`coef_malaysian_vs_singaporean`** is the fixed effect for Malaysian vs "
        "Singaporean (reference), holding other fixed predictors."
    )
    report.append("")

    res_df = pd.DataFrame(rows)
    if "success" in res_df.columns:
        ok = res_df[res_df["success"] == True].copy()
        if not ok.empty and "p_malaysian_vs_singaporean" in ok.columns:
            sig = ok[ok["p_malaysian_vs_singaporean"] < 0.05].sort_values("p_malaysian_vs_singaporean")
            report.append(f"- Significant Malaysian-vs-Singaporean effects (p<0.05): **{len(sig)}** / {len(ok)}")
            report.append("")
            if not sig.empty:
                report.append("### Smallest p-values")
                for _, r in sig.head(8).iterrows():
                    report.append(
                        f"- **{r['feature']}**: coef={r['coef_malaysian_vs_singaporean']:.4g}, "
                        f"p={r['p_malaysian_vs_singaporean']:.4g}"
                    )
                report.append("")

    (output_dir / "seame_nationality_prosody_report.md").write_text("\n".join(report), encoding="utf-8")

    # Optional coefficient plot (Malaysian vs Singaporean)
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plot_df = res_df[res_df["success"] == True].copy()
        if not plot_df.empty:
            plot_df = plot_df.sort_values("coef_malaysian_vs_singaporean")
            fig, ax = plt.subplots(figsize=(8, max(3.0, 0.35 * len(plot_df))))
            y = np.arange(len(plot_df))
            ax.barh(y, plot_df["coef_malaysian_vs_singaporean"].astype(float), color="#2c7fb8")
            ax.set_yticks(y)
            ax.set_yticklabels(plot_df["feature"])
            ax.axvline(0, color="black", linewidth=0.8)
            ax.set_xlabel("Coefficient: Malaysian vs Singaporean (reference)")
            ax.set_title("SEAME: speaker nationality fixed effects (MixedLM + speaker RE)")
            fig.tight_layout()
            fig_path = output_dir / "fig_seame_speaker_nationality_coefs.png"
            fig.savefig(fig_path, dpi=160)
            plt.close(fig)
    except Exception:
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="SEAME nationality vs prosody (diagnostics + speaker-level MeM)")
    p.add_argument(
        "--input",
        type=str,
        default="results/functional_anchors/seame/seame_integrated_features.csv",
    )
    p.add_argument(
        "--output-dir",
        type=str,
        default="results/interlocutor_nationality/seame",
    )
    p.add_argument("--n-features", type=int, default=15)
    p.add_argument("--group-var", type=str, default="speaker", help="Random intercept grouping (default speaker)")
    args = p.parse_args()

    run(
        input_csv=pathlib.Path(args.input),
        output_dir=pathlib.Path(args.output_dir),
        n_features=int(args.n_features),
        group_var=str(args.group_var),
    )
