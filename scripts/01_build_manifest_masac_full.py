#!/usr/bin/env python3
"""
Build MASAC manifest from compiled CSV with actual audio file paths.

This script:
1. Reads masac_data_compiled.csv
2. Finds actual audio files in masac_wav16k_clips subdirectories
3. Creates manifest for prosody analysis
"""

import argparse
import pathlib
import pandas as pd
import librosa

def find_audio_files(clips_dir):
    """Find all MASAC audio files and create mapping."""
    clips_path = pathlib.Path(clips_dir)
    if not clips_path.exists():
        return {}
    
    wav_files = list(clips_path.rglob("*.wav"))
    file_map = {}
    for wav_file in wav_files:
        file_id = wav_file.stem  # e.g., "test_168_3" or "train_1268_0"
        file_map[file_id] = str(wav_file)
    
    return file_map

def get_audio_duration(wav_path):
    """Get duration of audio file in seconds."""
    try:
        y, sr = librosa.load(wav_path, sr=None)
        return len(y) / sr
    except Exception as e:
        print(f"Warning: Could not get duration for {wav_path}: {e}")
        return None

def build_masac_manifest(csv_file, clips_dir, output_manifest, get_durations=True):
    """
    Build MASAC manifest from compiled CSV.
    
    Args:
        csv_file: Path to masac_data_compiled.csv
        clips_dir: Directory containing MASAC audio clips
        output_manifest: Path to output manifest CSV
        get_durations: Whether to compute audio file durations
    """
    print(f"Reading MASAC data from: {csv_file}")
    df = pd.read_csv(csv_file, low_memory=False)
    
    print(f"Total utterances in CSV: {len(df)}")
    
    # Find all audio files
    print(f"\nFinding audio files in {clips_dir}...")
    file_map = find_audio_files(clips_dir)
    print(f"Found {len(file_map)} audio files")
    
    # Map language labels
    lang_map = {
        'CSW': 'CS',
        'EN': 'EN',
        'HI': 'HI'
    }
    df['lang'] = df['Language'].map(lang_map).fillna('UNK')
    
    # Create condition labels
    def get_condition(lang):
        if lang == 'CS':
            return 'code_switched'
        elif lang == 'EN':
            return 'monolingual_EN'
        elif lang == 'HI':
            return 'monolingual_HI'
        else:
            return 'unknown'
    
    df['condition'] = df['lang'].apply(get_condition)
    
    # Filter out unknown language
    df = df[df['lang'] != 'UNK']
    
    # Build manifest rows
    print("\nBuilding manifest rows...")
    rows = []
    found_count = 0
    missing_count = 0
    
    for _, row in df.iterrows():
        file_name = row['name']  # e.g., "train_337_0.wav"
        file_id = file_name.replace('.wav', '')  # e.g., "train_337_0"
        
        # Find audio file
        wav_path = file_map.get(file_id)
        
        if not wav_path:
            missing_count += 1
            continue  # Skip if audio file not found
        
        found_count += 1
        
        # Get language and condition
        lang = row['lang']
        condition = row['condition']
        transcript = str(row.get('Transcript', ''))
        
        # For MASAC, each file is already an utterance, so start=0
        start_sec = 0.0
        end_sec = None
        
        if get_durations:
            duration = get_audio_duration(wav_path)
            if duration is not None:
                end_sec = duration
            else:
                continue  # Skip if we can't get duration
        else:
            end_sec = -1.0
        
        # Create utterance ID
        if end_sec and end_sec > 0:
            utt_id = f"{file_id}_{start_sec:.3f}_{end_sec:.3f}"
        else:
            utt_id = file_id
        
        rows.append({
            'utt_id': utt_id,
            'file_id': file_id,
            'wav': wav_path,
            'start': start_sec,
            'end': end_sec if end_sec else -1.0,
            'speaker': 'unknown',  # MASAC may not have speaker info
            'lang': lang,
            'condition': condition,
            'text': transcript,
        })
    
    manifest_df = pd.DataFrame(rows)
    
    if manifest_df.empty:
        print("\nERROR: No valid utterances found.")
        return None
    
    # Save manifest
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest_df.to_csv(output_manifest, index=False)
    
    print(f"\nWrote manifest to: {output_manifest}")
    print(f"  - Total utterances: {len(manifest_df)}")
    print(f"  - Found audio files: {found_count}")
    print(f"  - Missing audio files: {missing_count}")
    
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
    p = argparse.ArgumentParser(description='Build MASAC manifest from compiled CSV')
    p.add_argument('--csv', type=str,
                   default='data/masac_raw/masac_data_compiled.csv',
                   help='MASAC compiled CSV file')
    p.add_argument('--clips-dir', type=str,
                   default='data/masac_wav16k_clips',
                   help='Directory containing MASAC audio clips')
    p.add_argument('--output', type=str,
                   default='manifests/masac_manifest.csv',
                   help='Output manifest CSV')
    p.add_argument('--no-durations', action='store_true',
                   help='Skip computing audio durations')
    
    args = p.parse_args()
    
    csv_file = pathlib.Path(args.csv)
    clips_dir = pathlib.Path(args.clips_dir)
    output_file = pathlib.Path(args.output)
    
    if not csv_file.exists():
        print(f"ERROR: CSV file not found: {csv_file}")
        exit(1)
    
    if not clips_dir.exists():
        print(f"ERROR: Clips directory not found: {clips_dir}")
        exit(1)
    
    build_masac_manifest(csv_file, clips_dir, output_file, get_durations=not args.no_durations)

