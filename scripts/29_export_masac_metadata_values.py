#!/usr/bin/env python3
"""
Export MASAC metadata values currently used in modeling to a CSV template.

This helps manual completion of speaker-level metadata before reruns.
"""

import argparse
import pathlib

import pandas as pd


def export_template(manifest_with_metadata: str, output_csv: str) -> pd.DataFrame:
    df = pd.read_csv(manifest_with_metadata, low_memory=False)
    if "speaker_id" not in df.columns:
        raise ValueError("Expected 'speaker_id' column in manifest_with_metadata")

    cols = [
        "speaker_id",
        "speaker_raw",
        "gender",
        "age",
        "age_bucket",
        "nationality",
        "dialogue_act",
        "interaction_id",
    ]
    present = [c for c in cols if c in df.columns]

    # One row per speaker_id with currently active/default values.
    agg = (
        df.sort_values(by=["speaker_id"])
        .groupby("speaker_id", dropna=False)[present]
        .agg(lambda s: s.dropna().iloc[0] if len(s.dropna()) else "")
        .reset_index(drop=True)
    )
    # Add support columns to aid manual curation.
    counts = df.groupby("speaker_id").size().rename("n_utterances").reset_index()
    agg = counts.merge(agg, on="speaker_id", how="left")
    agg["notes"] = ""

    out = pathlib.Path(output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(out, index=False)
    print(f"Wrote MASAC metadata template: {out}")
    print(f"Speakers exported: {len(agg)}")
    return agg


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Export current MASAC metadata values template CSV")
    p.add_argument(
        "--manifest-with-metadata",
        type=str,
        default="results/functional_anchors/masac/masac_manifest_with_metadata.csv",
        help="Input MASAC manifest enriched with metadata",
    )
    p.add_argument(
        "--output",
        type=str,
        default="data/masac_raw/masac_speaker_metadata_values_current.csv",
        help="Output CSV for manual update",
    )
    args = p.parse_args()
    export_template(args.manifest_with_metadata, args.output)
