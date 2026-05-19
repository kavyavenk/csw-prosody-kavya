#!/usr/bin/env python3
"""
Preprocess and harmonize speaker/interaction metadata for modeling.

Adds normalized covariates for:
- gender
- age + age_bucket
- nationality
- dialogue_act
- interaction_id
- audience proficiency proxy (interaction-level L2 orientation)

Designed to run after switch directionality extraction and before feature integration.
"""

import argparse
import pathlib
from typing import Optional

import numpy as np
import pandas as pd


def normalize_gender(val) -> str:
    if pd.isna(val):
        return "unknown"
    s = str(val).strip().lower()
    if s in ("m", "male", "man"):
        return "male"
    if s in ("f", "female", "woman"):
        return "female"
    if s:
        return s
    return "unknown"


def normalize_nationality(val) -> str:
    if pd.isna(val):
        return "unknown"
    s = str(val).strip().lower()
    if not s:
        return "unknown"
    if "singapore" in s:
        return "singaporean"
    if "malaysia" in s:
        return "malaysian"
    if "india" in s or "indian" in s:
        return "indian"
    return s.replace(" ", "_")


def age_to_bucket(age_val, corpus: str) -> str:
    if pd.isna(age_val):
        return "unknown"
    try:
        age = float(age_val)
    except Exception:
        return "unknown"
    if corpus == "seame":
        if 19 <= age <= 24:
            return "19-24"
        if age < 19:
            return "<19"
        return "25+"
    if age < 18:
        return "<18"
    if age <= 24:
        return "18-24"
    if age <= 34:
        return "25-34"
    if age <= 44:
        return "35-44"
    return "45+"


def normalize_dialogue_act(val) -> str:
    if pd.isna(val):
        return "unknown"
    s = str(val).strip().lower()
    if not s:
        return "unknown"
    s = s.replace("/", "_").replace(" ", "_")
    return s


def _enrich_seame(base_df: pd.DataFrame, seame_csv: pathlib.Path) -> pd.DataFrame:
    seame = pd.read_csv(seame_csv, low_memory=False)
    # Support partial-info files that only contain row-level demographics.
    # When row_number is present but timing/file keys are missing, attach those keys
    # from the canonical SEAME annotation table.
    key_cols = {"file", "speaker", "start_time", "end_time"}
    if "row_number" in seame.columns and not key_cols.issubset(set(seame.columns)):
        canonical = pathlib.Path("data/SEAME/SEAME_data_annotation_new_2015_annotated_4_17_24.csv")
        if canonical.exists():
            canon_df = pd.read_csv(canonical, low_memory=False)
            canon_keep = [
                "row_number",
                "file",
                "speaker",
                "start_time",
                "end_time",
                "dialog_act",
                "conversation",
            ]
            canon_keep = [c for c in canon_keep if c in canon_df.columns]
            seame = canon_df[canon_keep].merge(seame, on="row_number", how="left")
    needed = [
        "file",
        "speaker",
        "start_time",
        "end_time",
        "age",
        "gender",
        "nationality",
        "dialog_act",
        "conversation",
    ]
    keep = [c for c in needed if c in seame.columns]
    tmp = seame[keep].copy()
    tmp["start"] = (tmp["start_time"] / 1000.0).round(3)
    tmp["end"] = (tmp["end_time"] / 1000.0).round(3)
    tmp = tmp.rename(columns={"file": "file_id", "conversation": "interaction_id_raw"})
    merged = base_df.merge(
        tmp,
        how="left",
        left_on=["file_id", "speaker", "start", "end"],
        right_on=["file_id", "speaker", "start", "end"],
    )
    return merged


def _enrich_masac(base_df: pd.DataFrame, masac_ann_csv: pathlib.Path) -> pd.DataFrame:
    ann = pd.read_csv(masac_ann_csv, low_memory=False)
    # MASAC has limited demographics; we keep unknown defaults when missing.
    keep = [
        "name",
        "Conversation",
        "Speaker",
        "Type of code-switching",
        "Length of turn",
    ]
    keep = [c for c in keep if c in ann.columns]
    tmp = ann[keep].copy()
    tmp["file_id"] = tmp["name"].astype(str).str.replace(".wav", "", regex=False)
    tmp = tmp.rename(
        columns={
            "Conversation": "interaction_id_raw",
            "Speaker": "speaker_raw_ann",
            "Type of code-switching": "dialog_act",
            "Length of turn": "turn_length_words",
        }
    )
    merged = base_df.merge(tmp.drop(columns=["name"], errors="ignore"), on="file_id", how="left")
    return merged


def add_audience_proficiency_proxy(df: pd.DataFrame, corpus: str) -> pd.DataFrame:
    # Approximate perceived audience proficiency by interaction-level L2 orientation.
    # L2 proxy:
    # - EN and CS utterances increase perceived EN proficiency in both corpora.
    is_l2_oriented = df["lang"].isin(["EN", "CS"]).astype(float)

    interaction_col = "interaction_id"
    if interaction_col not in df.columns:
        df[interaction_col] = df["file_id"].astype(str)

    ratio = (
        df.groupby(interaction_col, dropna=False)["lang"]
        .apply(lambda s: float(s.isin(["EN", "CS"]).mean()) if len(s) else np.nan)
        .rename("audience_l2_ratio")
    )
    df = df.merge(ratio, left_on=interaction_col, right_index=True, how="left")

    def ratio_bucket(x: float) -> str:
        if pd.isna(x):
            return "unknown"
        if x < 0.33:
            return "low_l2"
        if x < 0.66:
            return "mid_l2"
        return "high_l2"

    df["audience_proficiency_proxy"] = df["audience_l2_ratio"].apply(ratio_bucket)
    return df


def preprocess_metadata(
    manifest_in: str,
    manifest_out: str,
    corpus: str,
    seame_csv: Optional[str] = None,
    masac_annotations: Optional[str] = None,
) -> pd.DataFrame:
    df = pd.read_csv(manifest_in, low_memory=False)
    print(f"Loaded manifest rows: {len(df)}")

    if corpus == "seame":
        src = pathlib.Path(
            seame_csv or "data/SEAME/SEAME_data_annotation_new_2015_annotated_4_17_24.csv"
        )
        if not src.exists():
            raise FileNotFoundError(f"SEAME metadata CSV not found: {src}")
        df = _enrich_seame(df, src)
        df["age"] = pd.to_numeric(df.get("age"), errors="coerce")
        df["age_bucket"] = df["age"].apply(lambda x: age_to_bucket(x, "seame"))
        df["gender"] = df.get("gender", pd.Series(index=df.index)).apply(normalize_gender)
        df["nationality"] = df.get("nationality", pd.Series(index=df.index)).apply(
            normalize_nationality
        )
        df["dialogue_act"] = df.get("dialog_act", pd.Series(index=df.index)).apply(
            normalize_dialogue_act
        )
        df["interaction_id"] = (
            df.get("interaction_id_raw", pd.Series(index=df.index))
            .fillna(df["file_id"])
            .astype(str)
        )
    else:
        src = pathlib.Path(
            masac_annotations or "data/masac_raw/fixed_with_automated_annotations.csv"
        )
        if not src.exists():
            raise FileNotFoundError(f"MASAC annotation CSV not found: {src}")
        df = _enrich_masac(df, src)
        # MASAC currently lacks stable age/gender/nationality columns.
        df["age"] = np.nan
        df["age_bucket"] = "unknown"
        df["gender"] = "unknown"
        df["nationality"] = "unknown"
        df["dialogue_act"] = df.get("dialog_act", pd.Series(index=df.index)).apply(
            normalize_dialogue_act
        )
        df["interaction_id"] = (
            df.get("interaction_id_raw", pd.Series(index=df.index))
            .fillna(df["file_id"])
            .astype(str)
        )

    df = add_audience_proficiency_proxy(df, corpus)

    # Harmonize categorical blanks
    for col in ["age_bucket", "gender", "nationality", "dialogue_act", "interaction_id"]:
        df[col] = df[col].fillna("unknown").astype(str).replace({"": "unknown", "nan": "unknown"})

    out = pathlib.Path(manifest_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote enriched manifest: {out}")
    print(
        "Added columns: age, age_bucket, gender, nationality, dialogue_act, "
        "interaction_id, audience_l2_ratio, audience_proficiency_proxy"
    )
    return df


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Preprocess speaker/interaction metadata for modeling")
    p.add_argument("--manifest-in", type=str, required=True, help="Input manifest with directionality")
    p.add_argument("--manifest-out", type=str, required=True, help="Output enriched manifest")
    p.add_argument("--corpus", type=str, choices=["seame", "masac"], required=True)
    p.add_argument("--seame-csv", type=str, default=None, help="Optional SEAME source CSV")
    p.add_argument(
        "--masac-annotations",
        type=str,
        default=None,
        help="Optional MASAC annotations CSV",
    )
    args = p.parse_args()
    preprocess_metadata(
        manifest_in=args.manifest_in,
        manifest_out=args.manifest_out,
        corpus=args.corpus,
        seame_csv=args.seame_csv,
        masac_annotations=args.masac_annotations,
    )
