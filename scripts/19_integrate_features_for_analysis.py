#!/usr/bin/env python3
"""
Integrate all features and annotations for comprehensive analysis.

This script combines:
- Prosodic features (DisVoice)
- Discourse markers and repetitions
- Switch directionality
- Creates analysis-ready dataset
"""

import argparse
import pathlib
import pandas as pd
import numpy as np

_META_OVERLAP = ("speaker", "lang", "condition", "speaker_id", "speaker_raw", "text")


def integrate_features(feature_file: str, manifest_file: str, 
                      output_file: str, corpus: str):
    """
    Integrate all features into a single analysis-ready dataset.
    """
    print(f"Loading prosodic features from: {feature_file}")
    features_df = pd.read_csv(feature_file, low_memory=False)
    
    print(f"Loading annotated manifest from: {manifest_file}")
    manifest_df = pd.read_csv(manifest_file, low_memory=False)
    
    print(f"\nFeatures shape: {features_df.shape}")
    print(f"Manifest shape: {manifest_df.shape}")
    
    # Merge on utt_id (manifest wins for speaker / condition / lang)
    print("\nMerging features with manifest...")
    drop_cols = [c for c in _META_OVERLAP if c in features_df.columns]
    feat_trim = features_df.drop(columns=drop_cols, errors="ignore")
    df = feat_trim.merge(manifest_df, on="utt_id", how="inner")
    
    print(f"Integrated dataset shape: {df.shape}")
    
    # Create analysis variables
    print("\nCreating analysis variables...")
    
    # CSW vs monolingual binary
    df['is_csw'] = (df['lang'] == 'CS').astype(int)
    
    # Discourse marker binary (if available)
    if 'has_discourse_marker' in df.columns:
        df['has_dm'] = df['has_discourse_marker'].astype(int)
    else:
        df['has_dm'] = 0
    
    # Repetition binary (if available)
    if 'has_repetition' in df.columns:
        df['has_rep'] = df['has_repetition'].astype(int)
    else:
        df['has_rep'] = 0
    
    # Directionality (for CSW only)
    if 'switch_direction_class' in df.columns:
        df['is_l1_to_l2'] = (df['switch_direction_class'] == 'L1→L2').astype(int)
        df['is_l2_to_l1'] = (df['switch_direction_class'] == 'L2→L1').astype(int)
        # Set to NaN for non-CSW utterances
        df.loc[df['is_csw'] == 0, 'is_l1_to_l2'] = np.nan
        df.loc[df['is_csw'] == 0, 'is_l2_to_l1'] = np.nan
    else:
        df['is_l1_to_l2'] = np.nan
        df['is_l2_to_l1'] = np.nan
    
    # Interaction terms
    df['csw_x_dm'] = df['is_csw'] * df['has_dm']
    df['csw_x_rep'] = df['is_csw'] * df['has_rep']
    
    # Save integrated dataset
    output_path = pathlib.Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"\nSaved integrated dataset to: {output_file}")
    
    # Print summary statistics
    print("\n=== Dataset Summary ===")
    print(f"Total utterances: {len(df)}")
    print(f"CSW utterances: {df['is_csw'].sum()} ({100*df['is_csw'].mean():.1f}%)")
    
    if df['has_dm'].sum() > 0:
        print(f"Utterances with discourse markers: {df['has_dm'].sum()} "
              f"({100*df['has_dm'].mean():.1f}%)")
        print(f"  CSW with DM: {df[df['is_csw']==1]['has_dm'].sum()} "
              f"({100*df[df['is_csw']==1]['has_dm'].mean():.1f}%)")
        print(f"  Monolingual with DM: {df[df['is_csw']==0]['has_dm'].sum()} "
              f"({100*df[df['is_csw']==0]['has_dm'].mean():.1f}%)")
    
    if df['has_rep'].sum() > 0:
        print(f"Utterances with repetitions: {df['has_rep'].sum()} "
              f"({100*df['has_rep'].mean():.1f}%)")
    
    if df['is_l1_to_l2'].notna().sum() > 0:
        print(f"\nSwitch directionality (CSW only):")
        print(f"  L1→L2: {df['is_l1_to_l2'].sum()} "
              f"({100*df['is_l1_to_l2'].mean():.1f}% of CSW)")
        print(f"  L2→L1: {df['is_l2_to_l1'].sum()} "
              f"({100*df['is_l2_to_l1'].mean():.1f}% of CSW)")
    
    # Feature columns summary
    prosodic_cols = [c for c in df.columns if any(x in c.lower() 
                   for x in ['f0', 'pitch', 'energy', 'duration', 'rate', 'pause'])]
    print(f"\nProsodic features: {len(prosodic_cols)}")
    
    return df

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Integrate all features for analysis'
    )
    p.add_argument('--features', type=str, required=True,
                   help='Input prosodic features CSV')
    p.add_argument('--manifest', type=str, required=True,
                   help='Input annotated manifest CSV')
    p.add_argument('--output', type=str, required=True,
                   help='Output integrated CSV')
    p.add_argument('--corpus', type=str, choices=['seame', 'masac'],
                   required=True, help='Corpus name')
    
    args = p.parse_args()
    
    feature_file = pathlib.Path(args.features)
    manifest_file = pathlib.Path(args.manifest)
    
    if not feature_file.exists():
        print(f"ERROR: Feature file not found: {feature_file}")
        exit(1)
    
    if not manifest_file.exists():
        print(f"ERROR: Manifest file not found: {manifest_file}")
        exit(1)
    
    integrate_features(
        str(feature_file), str(manifest_file), args.output, args.corpus
    )
