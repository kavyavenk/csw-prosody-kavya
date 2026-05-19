#!/usr/bin/env python3
"""
Summarize interlocutor-gender findings (numbers + narrative).

Inputs are the outputs from `scripts/30_interlocutor_gender_effects.py`.
Writes a single combined markdown report.
"""

from __future__ import annotations

import argparse
import pathlib

import numpy as np
import pandas as pd


def _load_preview(preview_csv: pathlib.Path) -> pd.DataFrame:
    df = pd.read_csv(preview_csv, low_memory=False)
    for col in ["gender_match", "speaker_gender_mode", "interlocutor_gender"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df


def _load_models(models_csv: pathlib.Path) -> pd.DataFrame:
    df = pd.read_csv(models_csv, low_memory=False)
    return df


def _fmt_pct(n: int, d: int) -> str:
    if d == 0:
        return "0.0%"
    return f"{(100.0 * n / d):.1f}%"


def _summarize_one(corpus: str, models_csv: pathlib.Path, preview_csv: pathlib.Path) -> str:
    preview = _load_preview(preview_csv)
    models = _load_models(models_csv)

    n_rows = len(preview)
    gm_counts = preview["gender_match"].value_counts(dropna=False).to_dict() if "gender_match" in preview.columns else {}

    # Models
    ok = models[models.get("success", True) == True].copy() if "success" in models.columns else models.copy()
    ok["p_diff_vs_same"] = pd.to_numeric(ok.get("p_diff_vs_same"), errors="coerce")
    ok["coef_diff_vs_same"] = pd.to_numeric(ok.get("coef_diff_vs_same"), errors="coerce")
    ok = ok.dropna(subset=["p_diff_vs_same", "coef_diff_vs_same"])
    ok["abs_coef"] = ok["coef_diff_vs_same"].abs()

    # Significance
    sig_05 = ok[ok["p_diff_vs_same"] < 0.05].sort_values("p_diff_vs_same").copy()
    sig_001 = ok[ok["p_diff_vs_same"] < 0.001].sort_values("p_diff_vs_same").copy()

    # Effects direction
    n_lower = int((sig_05["coef_diff_vs_same"] < 0).sum())
    n_higher = int((sig_05["coef_diff_vs_same"] > 0).sum())

    lines: list[str] = []
    lines.append(f"## {corpus.upper()}")
    lines.append("")
    lines.append("### Data coverage")
    lines.append(f"- **Rows with interlocutor label**: {n_rows:,}")
    if gm_counts:
        same = int(gm_counts.get("same", 0))
        diff = int(gm_counts.get("different", 0))
        unk = int(gm_counts.get("unknown", 0))
        lines.append(f"- **Gender match distribution**:")
        lines.append(f"  - same: {same:,} ({_fmt_pct(same, n_rows)})")
        lines.append(f"  - different: {diff:,} ({_fmt_pct(diff, n_rows)})")
        lines.append(f"  - unknown: {unk:,} ({_fmt_pct(unk, n_rows)})")
    lines.append("")

    lines.append("### Model results (mixed-gender vs same-gender)")
    lines.append(f"- **Outcomes modeled**: {len(ok):,}")
    lines.append(f"- **Significant @ p<0.05**: {len(sig_05):,} (lower: {n_lower}, higher: {n_higher})")
    lines.append(f"- **Significant @ p<0.001**: {len(sig_001):,}")
    lines.append("")

    if len(sig_05):
        lines.append("#### Top effects (lowest p-values)")
        top = sig_05.head(10)
        for _, r in top.iterrows():
            feat = r["feature"]
            coef = float(r["coef_diff_vs_same"])
            p = float(r["p_diff_vs_same"])
            direction = "lower" if coef < 0 else "higher"
            lines.append(f"- **{feat}**: mixed-gender is **{direction}** by {coef:.3g} (p={p:.3g})")
        lines.append("")
    else:
        lines.append("- No outcomes reached p<0.05 in this exploratory set.")
        lines.append("")

    # Narrative interpretation (lightweight, but clear)
    lines.append("### Plain-language interpretation")
    if len(sig_05):
        if n_lower > n_higher:
            lines.append(
                "- Across the most variable prosody outcomes, **mixed-gender turns tended to show slightly lower values** "
                "than same-gender turns for several pitch-related measures."
            )
        else:
            lines.append(
                "- Across the most variable prosody outcomes, **mixed-gender turns tended to show slightly higher values** "
                "than same-gender turns for several measures."
            )
        lines.append(
            "- Treat this as **exploratory**: the operationalization is turn-adjacent (previous speaker), and results depend "
            "on which outcomes were selected (top variance)."
        )
    else:
        lines.append(
            "- With this definition of interlocutor (previous speaker), we **did not find reliable evidence** that same- vs mixed-gender "
            "turn adjacency systematically shifts these prosody measures in this run."
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize interlocutor-gender findings for SEAME + MASAC")
    p.add_argument("--seame-models", type=str, default="results/interlocutor_gender/seame_final/seame_interlocutor_gender_models.csv")
    p.add_argument("--seame-preview", type=str, default="results/interlocutor_gender/seame_final/seame_interlocutor_gender_labels.csv")
    p.add_argument("--masac-models", type=str, default="results/interlocutor_gender/masac_final/seame_interlocutor_gender_models.csv")
    p.add_argument("--masac-preview", type=str, default="results/interlocutor_gender/masac_final/seame_interlocutor_gender_labels.csv")
    p.add_argument("--out", type=str, default="results/interlocutor_gender/interlocutor_gender_findings.md")
    args = p.parse_args()

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    parts = []
    parts.append("# Interlocutor gender × prosody (SEAME + MASAC)")
    parts.append("")
    parts.append("These results use the **final MASAC metadata values** (age_bucket, nationality) from `data/masac_raw/masac_speaker_metadata_values_current.csv`.")
    parts.append("")
    parts.append("## What we tested")
    parts.append("- **Interlocutor gender** is defined as the gender of the **previous speaker turn** within an interaction.")
    parts.append("- We compare **mixed-gender** vs **same-gender** turn adjacency (`gender_match`).")
    parts.append("- Each outcome is modeled with `gender_match` plus basic controls (`condition`, `duration_sec`) and clustered SEs by speaker.")
    parts.append("")
    parts.append("## Caveats")
    parts.append("- Turn-adjacent ≠ necessarily addressee-directed.")
    parts.append("- Outcomes are selected as the **top-variance numeric prosody features** (not an exhaustive set).")
    parts.append("- p-values are uncorrected for multiple comparisons (exploratory).")
    parts.append("")

    parts.append(_summarize_one("seame", pathlib.Path(args.seame_models), pathlib.Path(args.seame_preview)))
    parts.append(_summarize_one("masac", pathlib.Path(args.masac_models), pathlib.Path(args.masac_preview)))

    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

