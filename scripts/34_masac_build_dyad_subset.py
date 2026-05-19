#!/usr/bin/env python3
"""
Build a dyad-only MASAC subset to better approximate "true interlocutor".

Heuristic:
- Exclude speakers marked as role/multi-party or multi-speaker in `masac_speaker_mapping.csv` notes.
- On the remaining utterances, keep only interactions (`interaction_id`) with exactly 2 distinct speakers.

Outputs:
- filtered integrated features CSV
"""

from __future__ import annotations

import argparse
import pathlib

import pandas as pd


def _load_excluded_speakers(mapping_csv: pathlib.Path) -> set[str]:
    m = pd.read_csv(mapping_csv, low_memory=False)
    notes = m.get("notes", pd.Series(index=m.index, dtype=str)).fillna("").astype(str).str.lower()
    # Exclude anything explicitly flagged as role/multi-party or multi-speaker
    bad = notes.str.contains("role/multi-party") | notes.str.contains("multi-speaker")
    excluded = set(m.loc[bad, "suggested_canonical"].dropna().astype(str).tolist())
    return excluded


def build(
    integrated_csv: pathlib.Path,
    mapping_csv: pathlib.Path,
    out_csv: pathlib.Path,
) -> pathlib.Path:
    df = pd.read_csv(integrated_csv, low_memory=False)

    for col in ["interaction_id", "speaker_id", "utt_id"]:
        if col not in df.columns:
            raise ValueError(f"Integrated CSV missing required column: {col}")

    excluded = _load_excluded_speakers(mapping_csv)

    keep = df[~df["speaker_id"].astype(str).isin(excluded)].copy()

    # Keep dyad interactions only
    n_spk = keep.groupby("interaction_id")["speaker_id"].nunique().rename("n_speakers")
    keep = keep.merge(n_spk, left_on="interaction_id", right_index=True, how="left")
    keep = keep[keep["n_speakers"] == 2].drop(columns=["n_speakers"])

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    keep.to_csv(out_csv, index=False)
    return out_csv


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Build dyad-only MASAC subset")
    p.add_argument(
        "--integrated",
        type=str,
        default="results/functional_anchors/masac/masac_integrated_features.csv",
    )
    p.add_argument(
        "--mapping",
        type=str,
        default="data/masac_raw/masac_speaker_mapping.csv",
    )
    p.add_argument(
        "--out",
        type=str,
        default="results/interlocutor_gender/masac_dyad/masac_integrated_features_dyad.csv",
    )
    args = p.parse_args()

    dest = build(
        integrated_csv=pathlib.Path(args.integrated),
        mapping_csv=pathlib.Path(args.mapping),
        out_csv=pathlib.Path(args.out),
    )
    print(f"Wrote {dest}")

