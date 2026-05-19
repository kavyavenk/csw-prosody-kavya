#!/usr/bin/env python3
"""
Join canonical speaker IDs from masac_speaker_mapping.csv onto the MASAC manifest.

Uses:
- data/masac_raw/fixed_with_automated_annotations.csv (name, Speaker)
- data/masac_raw/masac_speaker_mapping.csv (raw_speaker -> suggested_canonical)

Adds/updates: speaker_raw, speaker_id, speaker (speaker == speaker_id for MeM groups).
"""

import argparse
import pathlib

import pandas as pd


def load_raw_to_canonical(mapping_path: pathlib.Path) -> dict:
    m = pd.read_csv(mapping_path)
    out = {}
    for _, r in m.iterrows():
        raw = str(r["raw_speaker"]).strip()
        canon = r["suggested_canonical"]
        if pd.isna(canon) or str(canon).strip() == "":
            canon = raw
        else:
            canon = str(canon).strip()
        out[raw] = canon
        out[raw.upper()] = canon
    return out


def apply_speaker(
    manifest_path: pathlib.Path,
    annotations_path: pathlib.Path,
    mapping_path: pathlib.Path,
    output_path: pathlib.Path,
) -> pd.DataFrame:
    ann = pd.read_csv(annotations_path, low_memory=False)
    if "Speaker" not in ann.columns or "name" not in ann.columns:
        raise ValueError("Annotations file must have columns: name, Speaker")

    name_to_raw = dict(
        zip(ann["name"].astype(str), ann["Speaker"].astype(str).str.strip())
    )
    raw_to_id = load_raw_to_canonical(mapping_path)

    manifest = pd.read_csv(manifest_path, low_memory=False)
    speaker_raw_list = []
    speaker_id_list = []

    for _, row in manifest.iterrows():
        file_id = str(row.get("file_id", "")).strip()
        fname = f"{file_id}.wav" if file_id else ""
        raw = name_to_raw.get(fname, "UNKNOWN")
        if raw in ("", "nan", "None"):
            raw = "UNKNOWN"
        sid = raw_to_id.get(raw, raw_to_id.get(raw.upper() if raw else "", raw))
        speaker_raw_list.append(raw)
        speaker_id_list.append(sid)

    manifest["speaker_raw"] = speaker_raw_list
    manifest["speaker_id"] = speaker_id_list
    manifest["speaker"] = manifest["speaker_id"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(output_path, index=False)

    n_unique = manifest["speaker_id"].nunique()
    print(f"Wrote {len(manifest)} rows to {output_path}")
    print(f"  Unique speaker_id: {n_unique}")
    print(manifest["speaker_id"].value_counts().head(10))
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Apply canonical MASAC speaker IDs to manifest")
    p.add_argument(
        "--manifest",
        type=str,
        default="manifests/masac_manifest.csv",
        help="Input manifest CSV",
    )
    p.add_argument(
        "--annotations",
        type=str,
        default="data/masac_raw/fixed_with_automated_annotations.csv",
        help="MASAC annotations with name + Speaker",
    )
    p.add_argument(
        "--mapping",
        type=str,
        default="data/masac_raw/masac_speaker_mapping.csv",
        help="raw_speaker -> suggested_canonical mapping",
    )
    p.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output manifest (default: overwrite --manifest)",
    )
    args = p.parse_args()

    out = pathlib.Path(args.output or args.manifest)
    apply_speaker(
        pathlib.Path(args.manifest),
        pathlib.Path(args.annotations),
        pathlib.Path(args.mapping),
        out,
    )
