#!/usr/bin/env python3
"""
Refresh MASAC integrated features with the *final* metadata values.

This overwrites/creates `age_bucket` and `nationality` (and optionally `gender`) in the
integrated features table using `data/masac_raw/masac_speaker_metadata_values_current.csv`
matched on `speaker_id` (or `speaker` as fallback).
"""

from __future__ import annotations

import argparse
import pathlib

import pandas as pd


def refresh(
    integrated_csv: pathlib.Path,
    metadata_csv: pathlib.Path,
    out_csv: pathlib.Path | None = None,
    overwrite_gender: bool = False,
) -> pathlib.Path:
    df = pd.read_csv(integrated_csv, low_memory=False)
    meta = pd.read_csv(metadata_csv, low_memory=False)

    for c in ["speaker_id", "age_bucket", "nationality"]:
        if c not in meta.columns:
            raise ValueError(f"metadata_csv missing required column: {c}")

    meta = meta[["speaker_id", "gender", "age_bucket", "nationality"]].copy()
    meta["speaker_id"] = meta["speaker_id"].astype(str)

    # Choose join key
    join_key = "speaker_id" if "speaker_id" in df.columns else ("speaker" if "speaker" in df.columns else None)
    if join_key is None:
        raise ValueError("integrated_csv missing speaker_id and speaker columns")

    df[join_key] = df[join_key].astype(str)

    out = df.merge(meta, how="left", left_on=join_key, right_on="speaker_id", suffixes=("", "_meta"))

    # Fill/overwrite
    for col in ["age_bucket", "nationality"]:
        if f"{col}_meta" in out.columns:
            out[col] = out[f"{col}_meta"].where(out[f"{col}_meta"].notna(), out.get(col))
            out = out.drop(columns=[f"{col}_meta"])

    if overwrite_gender and "gender_meta" in out.columns:
        out["gender"] = out["gender_meta"].where(out["gender_meta"].notna(), out.get("gender"))
    if "gender_meta" in out.columns:
        out = out.drop(columns=["gender_meta"])

    # Drop the right-side speaker_id if we joined on speaker
    if join_key != "speaker_id" and "speaker_id_y" in out.columns:
        out = out.drop(columns=["speaker_id_y"])
    if "speaker_id_x" in out.columns:
        out = out.rename(columns={"speaker_id_x": "speaker_id"})

    dest = out_csv or integrated_csv
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)
    return dest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Refresh MASAC integrated metadata values")
    p.add_argument(
        "--integrated",
        type=str,
        default="results/functional_anchors/masac/masac_integrated_features.csv",
        help="MASAC integrated features CSV",
    )
    p.add_argument(
        "--metadata",
        type=str,
        default="data/masac_raw/masac_speaker_metadata_values_current.csv",
        help="Final MASAC speaker metadata values CSV",
    )
    p.add_argument("--out", type=str, default=None, help="Optional output path (else overwrite)")
    p.add_argument(
        "--overwrite-gender",
        action="store_true",
        help="If set, overwrite gender from metadata as well",
    )
    args = p.parse_args()

    dest = refresh(
        integrated_csv=pathlib.Path(args.integrated),
        metadata_csv=pathlib.Path(args.metadata),
        out_csv=pathlib.Path(args.out) if args.out else None,
        overwrite_gender=bool(args.overwrite_gender),
    )
    print(f"Wrote: {dest}")

