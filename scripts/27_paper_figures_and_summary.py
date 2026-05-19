#!/usr/bin/env python3
"""
Paper-oriented outputs: parse MeM result text → long CSV, build cross-corpus figures
from OLS directionality long table, write a short analysis overview for writing.

Inputs (defaults):
  results/mixed_effects/{masac,seame}_full/*_mixed_effects_results.txt
  results/cross_corpus/directionality_comparison_long.csv

Outputs:
  results/paper/mixed_effects_fixed_effects_long.csv
  results/paper/TABLE1_PRIMARY_MIXED_EFFECTS.md
  results/paper/figures/fig_ols_discourse_marker_by_feature.png
  results/paper/figures/fig_ols_repetition_by_feature.png
  results/paper/figures/fig_ols_cs_direction_key_terms.png
  results/paper/figures/fig_mem_discourse_marker_by_feature.png
  results/paper/PAPER_ANALYSIS_OVERVIEW.md (includes Table 1)
"""

from __future__ import annotations

import argparse
import pathlib
import re
from typing import List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FE_LINE = re.compile(
    r"^\s+(?P<term>[^:]+):\s+(?P<coef>[-+eE0-9.]+)\s+\(p=(?P<pval>[0-9.eE+-]+)\)"
)
FEATURE_HDR = re.compile(r"^Feature:\s*(.+)\s*$")

TERM_INTERCEPT = "Intercept"
TERM_MONO_EN = "C(condition)[T.monolingual_EN]"
TERM_MONO_HI = "C(condition)[T.monolingual_HI]"
TERM_MONO_ZH = "C(condition)[T.monolingual_ZH]"
TERM_DM = "has_discourse_marker[T.True]"
TERM_REP = "has_repetition[T.True]"
TERM_GROUP = "Group Var"

# Primary outcomes for Table 1 (report / thesis).
TABLE1_FEATURES = ["F0msemax", "F0tiltmin", "F0max", "F0avg"]


def _fmt_cell(mem_long: pd.DataFrame, corpus: str, feature: str, term: str) -> str:
    sub = mem_long[
        (mem_long["corpus"] == corpus)
        & (mem_long["feature"] == feature)
        & (mem_long["term"] == term)
    ]
    if sub.empty:
        return "—"
    c = float(sub.iloc[0]["coef"])
    p = float(sub.iloc[0]["p_value"])
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
    # Compact: coefficient + stars; p in parentheses
    return f"{c:.4f}{sig} (*p* = {p:.4g})"


def build_table1_markdown(mem_long: pd.DataFrame) -> str:
    """Markdown Table 1: selected features × MixedLM fixed effects, both corpora."""
    lines = [
        "## Table 1. Primary mixed-effects coefficients (speaker random intercept)",
        "",
        "**Model:** `outcome ~ C(condition) + has_discourse_marker + has_repetition` + random intercept for speaker. **Reference level for `condition`:** code-switched (CS). Coefficients are **additive adjustments** relative to that reference (monolingual rows compare mono vs CS; DM and Rep compare True vs False). **Units** are DisVoice’s native scale for each outcome—compare within a column/outcome, not across different outcome names.",
        "",
        "**Sample (current run):** MASAC *N* = 6,476 utterances, 84 speaker groups; SEAME *N* = 52,313 utterances, 65 speaker groups.",
        "",
        "| Outcome | Corpus | Intercept | Mono EN vs CS | Mono L1 vs CS | Discourse marker | Repetition | Speaker RE (Group Var) |",
        "|---------|--------|-----------|----------------|---------------|------------------|------------|-------------------------|",
    ]
    for feat in TABLE1_FEATURES:
        for corpus, mono_l1_term, l1_label in (
            ("masac", TERM_MONO_HI, "HI"),
            ("seame", TERM_MONO_ZH, "ZH"),
        ):
            if mem_long.empty:
                break
            any_fit = (
                len(mem_long[(mem_long["corpus"] == corpus) & (mem_long["feature"] == feat)]) > 0
            )
            if not any_fit:
                lines.append(
                    f"| **{feat}** | **{corpus.upper()}** | — | — | — | — | — | — |"
                )
                continue
            ic = _fmt_cell(mem_long, corpus, feat, TERM_INTERCEPT)
            en = _fmt_cell(mem_long, corpus, feat, TERM_MONO_EN)
            l1 = _fmt_cell(mem_long, corpus, feat, mono_l1_term)
            dm = _fmt_cell(mem_long, corpus, feat, TERM_DM)
            rp = _fmt_cell(mem_long, corpus, feat, TERM_REP)
            gv = _fmt_cell(mem_long, corpus, feat, TERM_GROUP)
            lines.append(
                f"| **{feat}** | **{corpus.upper()}** | {ic} | {en} | {l1} ({l1_label}) | {dm} | {rp} | {gv} |"
            )
    lines.extend(
        [
            "",
            "**Significance:** \\* *p* &lt; 0.05, \\*\\* *p* &lt; 0.01, \\*\\*\\* *p* &lt; 0.001 (appended to coefficient).",
            "",
            "**Note:** A row of em dashes means that outcome was **not** in the variance-selected feature list for that corpus in the latest `scripts/18_mixed_effects_analysis.py` run (e.g. **MASAC `F0avg`** here). Re-run with a forced feature list if you need that cell filled.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_mixed_effects_txt(path: pathlib.Path, corpus: str) -> pd.DataFrame:
    rows: List[dict] = []
    current_feature: Optional[str] = None
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in text:
        m_feat = FEATURE_HDR.match(line)
        if m_feat:
            current_feature = m_feat.group(1).strip()
            continue
        m = FE_LINE.match(line)
        if not m or current_feature is None:
            continue
        term = m.group("term").strip()
        try:
            coef = float(m.group("coef"))
            pval = float(m.group("pval"))
        except ValueError:
            continue
        rows.append(
            {
                "corpus": corpus,
                "feature": current_feature,
                "term": term,
                "coef": coef,
                "p_value": pval,
            }
        )
    return pd.DataFrame(rows)


def plot_ols_term_by_feature(
    long: pd.DataFrame,
    model_type: str,
    terms: List[str],
    title: str,
    out_path: pathlib.Path,
    max_features: int = 12,
    compound_row: bool = False,
) -> None:
    sub = long[(long["model_type"] == model_type) & (long["term"].isin(terms))].copy()
    if sub.empty:
        return
    if compound_row:
        sub["_row"] = sub["feature"] + " | " + sub["term"].str.replace(r"\[T\.True\]", "", regex=True)
        row_key = "_row"
    else:
        row_key = "feature"
    feats = sub[row_key].unique().tolist()
    if len(feats) > max_features:
        agg = sub.groupby(row_key)["coef"].apply(lambda s: np.nanmax(np.abs(s)))
        feats = agg.nlargest(max_features).index.tolist()
        sub = sub[sub[row_key].isin(feats)]
    sub = sub.sort_values(row_key)
    n_feat = len(sub[row_key].unique())
    fig_h = max(4, min(14, 0.32 * n_feat + 2))
    fig, ax = plt.subplots(figsize=(8, fig_h))
    pivot = sub.pivot_table(index=row_key, columns="corpus", values="coef", aggfunc="first")
    pivot = pivot.reindex(sorted(pivot.index))
    x = np.arange(len(pivot))
    w = 0.35
    corpora = [c for c in ("masac", "seame") if c in pivot.columns]
    for i, corp in enumerate(corpora):
        offset = (i - len(corpora) / 2 + 0.5) * w
        ax.barh(x + offset, pivot[corp].values, w, label=corp)
    ax.set_yticks(x)
    ax.set_yticklabels(pivot.index, fontsize=7)
    ax.axvline(0, color="0.4", linewidth=0.8)
    ax.set_xlabel("Coefficient (OLS)")
    ax.set_title(title)
    ax.legend(frameon=False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_mem_term_by_feature(
    mem_long: pd.DataFrame,
    term_substr: str,
    title: str,
    out_path: pathlib.Path,
    max_features: int = 12,
) -> None:
    sub = mem_long[mem_long["term"].str.contains(term_substr, regex=False)].copy()
    if sub.empty:
        return
    feats = sub["feature"].unique().tolist()
    if len(feats) > max_features:
        agg = sub.groupby("feature")["coef"].apply(lambda s: np.nanmax(np.abs(s)))
        feats = agg.nlargest(max_features).index.tolist()
        sub = sub[sub["feature"].isin(feats)]
    sub = sub.sort_values("feature")
    n_feat = len(sub["feature"].unique())
    fig_h = max(4, min(10, 0.35 * n_feat + 2))
    fig, ax = plt.subplots(figsize=(8, fig_h))
    pivot = sub.pivot_table(index="feature", columns="corpus", values="coef", aggfunc="first")
    pivot = pivot.reindex(sorted(pivot.index))
    x = np.arange(len(pivot))
    w = 0.35
    corpora = [c for c in ("masac", "seame") if c in pivot.columns]
    for i, corp in enumerate(corpora):
        offset = (i - len(corpora) / 2 + 0.5) * w
        vals = pivot[corp].values.astype(float)
        ax.barh(x + offset, vals, w, label=corp)
    ax.set_yticks(x)
    ax.set_yticklabels(pivot.index, fontsize=8)
    ax.axvline(0, color="0.4", linewidth=0.8)
    ax.set_xlabel("Coefficient (MixedLM fixed effect)")
    ax.set_title(title)
    ax.legend(frameon=False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def write_overview(
    paper_dir: pathlib.Path,
    mem_long: pd.DataFrame,
    ols_long: pd.DataFrame,
    table1_md: str,
) -> None:
    n_mem = len(mem_long)
    n_ols = len(ols_long)
    lines = [
        "# Paper-oriented analysis overview",
        "",
        "Auto-generated by `scripts/27_paper_figures_and_summary.py`. Edit for submission; numbers refresh when you re-run the script.",
        "",
        "## What to cite as primary inferential results",
        "",
        "1. **Mixed-effects (speaker random intercept):** `results/mixed_effects/masac_full/masac_mixed_effects_results.txt` and `results/mixed_effects/seame_full/seame_mixed_effects_results.txt`. Formula: `feature ~ condition + has_discourse_marker + has_repetition`. Reference level for condition is **code-switched**.",
        "2. **OLS (no speaker clustering):** `results/directionality_models/*/` — all-utterance **condition** models and **CS-only** models with **switch direction** and **DM × direction**. Use for direction hypotheses; use MeM for speaker-adjusted condition and anchors.",
        "",
        table1_md,
        "## Exported tables for plotting / supplements",
        "",
        f"- `results/paper/mixed_effects_fixed_effects_long.csv` — **{n_mem}** rows (parsed fixed effects + Group Var lines from MeM text).",
        f"- `results/cross_corpus/directionality_comparison_long.csv` — **{n_ols}** rows (flattened OLS).",
        f"- `TABLE1_PRIMARY_MIXED_EFFECTS.md` — standalone copy of Table 1 (for appendices / Word import).",
        "",
        "## Figures (this run)",
        "",
        "- `figures/fig_ols_discourse_marker_by_feature.png` — OLS `has_discourse_marker` coefficient, MASAC vs SEAME, **all_condition** model.",
        "- `figures/fig_ols_repetition_by_feature.png` — OLS `has_repetition`, same.",
        "- `figures/fig_ols_cs_direction_key_terms.png` — CS-only OLS: `is_l1_to_l2`, interaction, DM, repetition (where present).",
        "- `figures/fig_mem_discourse_marker_by_feature.png` — MeM fixed effect for discourse marker by feature (both corpora).",
        "- `figures/fig_mem_repetition_by_feature.png` — MeM fixed effect for repetition by feature.",
        "",
        "## Methods reminders for the paper",
        "",
        "- **SEAME switch direction** when no gold word LID: inferred from manifest **word list** (Latin-shaped token → EN, else ZH) in `scripts/17_extract_switch_directionality.py`; validate or replace if gold tags become available.",
        "- **Multiple features:** variance-ranked automatic selection; consider **pre-registered primary outcomes** or **FDR** across a declared family.",
        "",
    ]
    (paper_dir / "PAPER_ANALYSIS_OVERVIEW.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Paper figures + MeM long export + overview")
    p.add_argument("--paper-dir", type=str, default="results/paper")
    p.add_argument("--cross-corpus-dir", type=str, default="results/cross_corpus")
    p.add_argument(
        "--masac-mem",
        type=str,
        default="results/mixed_effects/masac_full/masac_mixed_effects_results.txt",
    )
    p.add_argument(
        "--seame-mem",
        type=str,
        default="results/mixed_effects/seame_full/seame_mixed_effects_results.txt",
    )
    args = p.parse_args()
    paper_dir = pathlib.Path(args.paper_dir)
    fig_dir = paper_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    masac_path = pathlib.Path(args.masac_mem)
    seame_path = pathlib.Path(args.seame_mem)
    mem_parts = []
    if masac_path.exists():
        mem_parts.append(parse_mixed_effects_txt(masac_path, "masac"))
    if seame_path.exists():
        mem_parts.append(parse_mixed_effects_txt(seame_path, "seame"))
    mem_long = pd.concat(mem_parts, ignore_index=True) if mem_parts else pd.DataFrame()
    if not mem_long.empty:
        mem_long.to_csv(paper_dir / "mixed_effects_fixed_effects_long.csv", index=False)
        print(f"Wrote {len(mem_long)} rows to {paper_dir / 'mixed_effects_fixed_effects_long.csv'}")

    ols_path = pathlib.Path(args.cross_corpus_dir) / "directionality_comparison_long.csv"
    ols_long = pd.read_csv(ols_path) if ols_path.exists() else pd.DataFrame()
    if ols_long.empty:
        print("WARN: no directionality_comparison_long.csv — run scripts/26_cross_corpus_comparison.py")

    dm_term = "has_discourse_marker[T.True]"
    rep_term = "has_repetition[T.True]"
    if not ols_long.empty:
        plot_ols_term_by_feature(
            ols_long,
            "all_condition",
            [dm_term],
            "OLS: discourse marker (all utterances)",
            fig_dir / "fig_ols_discourse_marker_by_feature.png",
        )
        plot_ols_term_by_feature(
            ols_long,
            "all_condition",
            [rep_term],
            "OLS: repetition (all utterances)",
            fig_dir / "fig_ols_repetition_by_feature.png",
        )
        cs_terms = [
            t
            for t in ols_long[ols_long["model_type"] == "cs_directionality"]["term"].unique()
            if t != "Intercept"
        ]
        plot_ols_term_by_feature(
            ols_long,
            "cs_directionality",
            cs_terms[:12],
            "OLS: CS-only directionality (by feature × term)",
            fig_dir / "fig_ols_cs_direction_key_terms.png",
            compound_row=True,
        )
        print(f"Wrote OLS figures under {fig_dir}")

    if not mem_long.empty:
        plot_mem_term_by_feature(
            mem_long,
            "has_discourse_marker",
            "MixedLM: discourse marker fixed effect",
            fig_dir / "fig_mem_discourse_marker_by_feature.png",
        )
        plot_mem_term_by_feature(
            mem_long,
            "has_repetition",
            "MixedLM: repetition fixed effect",
            fig_dir / "fig_mem_repetition_by_feature.png",
        )
        print(f"Wrote MeM figures under {fig_dir}")

    table1_md = build_table1_markdown(mem_long) if not mem_long.empty else "## Table 1.\n\n*(No mixed-effects long table parsed.)*\n\n"
    write_overview(paper_dir, mem_long, ols_long, table1_md)
    (paper_dir / "TABLE1_PRIMARY_MIXED_EFFECTS.md").write_text(
        "# Table 1. Primary mixed-effects coefficients\n\n" + table1_md + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {paper_dir / 'PAPER_ANALYSIS_OVERVIEW.md'}")
    print(f"Wrote {paper_dir / 'TABLE1_PRIMARY_MIXED_EFFECTS.md'}")


if __name__ == "__main__":
    main()
