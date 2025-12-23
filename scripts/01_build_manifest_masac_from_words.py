#!/usr/bin/env python3
"""
Build MASAC manifest from word-level annotations.

This script:
1. Reads the word-level CSV with updated language tags
2. Aggregates word-level tags to utterance-level language labels
3. Builds a manifest for prosody analysis

Usage:
    python scripts/01_build_manifest_masac_from_words.py --words masac_words_sample.csv
"""

import argparse
import pathlib
import pandas as pd
import librosa
import numpy as np

def get_audio_duration(wav_path):
    """Get duration of audio file in seconds."""
    try:
        y, sr = librosa.load(wav_path, sr=None)
        return len(y) / sr
    except Exception as e:
        print(f"Warning: Could not get duration for {wav_path}: {e}")
        return None

def aggregate_utterance_lang(word_df):
    """
    Aggregate word-level language tags to utterance-level labels.
    
    An utterance is CSW if it contains both EN and HI words (excluding OTHER).
    Otherwise, it's monolingual EN or HI.
    """
    utterance_langs = {}
    
    for _, row in word_df.iterrows():
        file_id = row['file_id']
        utterance_idx = row['utterance_idx']
        lang_tag = row['language_tag']
        
        key = (file_id, utterance_idx)
        if key not in utterance_langs:
            utterance_langs[key] = {'EN': 0, 'HI': 0, 'OTHER': 0}
        
        if lang_tag in ['EN', 'HI', 'OTHER']:
            utterance_langs[key][lang_tag] += 1
    
    # Determine utterance-level language
    utterance_labels = {}
    for key, counts in utterance_langs.items():
        has_en = counts['EN'] > 0
        has_hi = counts['HI'] > 0
        
        if has_en and has_hi:
            lang = 'CS'  # Code-switched
        elif has_en:
            lang = 'EN'  # Monolingual English
        elif has_hi:
            lang = 'HI'  # Monolingual Hindi
        else:
            lang = 'OTHER'  # Only punctuation/other
        
        utterance_labels[key] = lang
    
    return utterance_labels

def build_manifest_from_words(word_csv, wav_dir, output_manifest, get_durations=True):
    """
    Build manifest from word-level annotations.
    
    Args:
        word_csv: Path to word-level CSV with language tags
        wav_dir: Directory containing WAV files
        output_manifest: Path to output manifest CSV
        get_durations: Whether to compute audio file durations
    """
    print(f"Reading word-level annotations from: {word_csv}")
    word_df = pd.read_csv(word_csv)
    
    print(f"Found {len(word_df)} word-level annotations")
    print(f"  - Files: {word_df['file_id'].nunique()}")
    print(f"  - Utterances: {word_df.groupby(['file_id', 'utterance_idx']).ngroups}")
    
    # Aggregate to utterance-level language labels
    print("\nAggregating word-level tags to utterance-level labels...")
    utterance_labels = aggregate_utterance_lang(word_df)
    
    # Get unique utterances
    utterances = word_df.groupby(['file_id', 'utterance_idx']).first().reset_index()
    
    # Build manifest rows
    print("\nBuilding manifest...")
    rows = []
    wav_path = pathlib.Path(wav_dir)
    
    for _, row in utterances.iterrows():
        file_id = row['file_id']
        utterance_idx = row['utterance_idx']
        transcript = row.get('transcript', '')
        
        # Get utterance-level language label
        key = (file_id, utterance_idx)
        lang = utterance_labels.get(key, 'UNK')
        
        if lang == 'OTHER' or lang == 'UNK':
            continue  # Skip utterances with only punctuation or unknown
        
        # Determine condition
        if lang == 'CS':
            condition = 'code_switched'
        elif lang == 'EN':
            condition = 'monolingual_EN'
        elif lang == 'HI':
            condition = 'monolingual_HI'
        else:
            continue
        
        # Build WAV path - MASAC files are individual utterance files
        # Remove .wav extension if present
        file_id_clean = file_id.replace('.wav', '')
        wav_file = wav_path / f"{file_id_clean}.wav"
        
        # For MASAC, each file is a separate utterance, so start=0
        # We'll get duration from the audio file if available
        start_sec = 0.0
        end_sec = -1.0  # Default to -1 if duration unknown
        
        if get_durations and wav_path.exists() and wav_file.exists():
            duration = get_audio_duration(str(wav_file))
            if duration is not None:
                end_sec = duration
        # If file doesn't exist, we'll still include it in manifest with end=-1
        # The audio processing can happen later when files are available
        
        # Create utterance ID
        if end_sec is not None:
            utt_id = f"{file_id_clean}_{start_sec:.3f}_{end_sec:.3f}"
        else:
            utt_id = file_id_clean
        
        rows.append({
            'utt_id': utt_id,
            'file_id': file_id_clean,
            'wav': str(wav_file),
            'start': start_sec,
            'end': end_sec if end_sec is not None else -1.0,
            'speaker': 'unknown',  # MASAC may not have speaker info
            'lang': lang,
            'condition': condition,
            'text': transcript,
        })
    
    manifest_df = pd.DataFrame(rows)
    
    if manifest_df.empty:
        print("\nERROR: No valid utterances found. Check:")
        print("  - Word-level annotations")
        print("  - Language tag aggregation")
        return None
    
    # Save manifest
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest_df.to_csv(output_manifest, index=False)
    
    print(f"\nWrote manifest to: {output_manifest}")
    print(f"  - Total utterances: {len(manifest_df)}")
    print(f"\nLanguage distribution:")
    lang_counts = manifest_df['lang'].value_counts()
    for lang, count in lang_counts.items():
        pct = 100 * count / len(manifest_df)
        print(f"  {lang}: {count} ({pct:.1f}%)")
    
    print(f"\nCondition distribution:")
    cond_counts = manifest_df['condition'].value_counts()
    for cond, count in cond_counts.items():
        pct = 100 * count / len(manifest_df)
        print(f"  {cond}: {count} ({pct:.1f}%)")
    
    return manifest_df

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Build MASAC manifest from word-level annotations')
    p.add_argument('--words', type=str,
                   default='data/masac_raw/masac_words_sample.csv',
                   help='Word-level CSV with language tags')
    p.add_argument('--wav-dir', type=str,
                   default='data/masac_wav16k',
                   help='Directory containing WAV files')
    p.add_argument('--output', type=str,
                   default='manifests/masac_manifest.csv',
                   help='Output manifest CSV')
    p.add_argument('--no-durations', action='store_true',
                   help='Skip computing audio durations (use -1.0)')
    
    args = p.parse_args()
    
    word_file = pathlib.Path(args.words)
    wav_dir = pathlib.Path(args.wav_dir)
    output_file = pathlib.Path(args.output)
    
    if not word_file.exists():
        print(f"ERROR: Word file not found: {word_file}")
        exit(1)
    
    if not wav_dir.exists():
        print(f"WARNING: WAV directory not found: {wav_dir}")
        print("  Manifest will be created but may have missing files")
    
    build_manifest_from_words(
        word_file,
        wav_dir,
        output_file,
        get_durations=not args.no_durations
    )

