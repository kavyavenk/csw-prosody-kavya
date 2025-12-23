#!/usr/bin/env python3
"""
Build SEAME manifest for prosody analysis.

Reads SEAME CSV and creates manifest with proper column mapping.
"""

import argparse
import pathlib
import pandas as pd

def build_seame_manifest(csv_file, wav_dir, output_manifest):
    """
    Build SEAME manifest from CSV file.
    
    Args:
        csv_file: Path to SEAME_data_annotation_new_2015_annotated_4_17_24.csv
        wav_dir: Directory containing SEAME WAV files
        output_manifest: Path to output manifest CSV
    """
    print(f"Reading SEAME data from: {csv_file}")
    df = pd.read_csv(csv_file, low_memory=False)
    
    print(f"Total rows in CSV: {len(df)}")
    
    # Check required columns
    required_cols = ['file', 'start_time', 'end_time', 'speaker', 'language']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        print(f"Available columns: {list(df.columns)}")
        return None
    
    # Convert timestamps from milliseconds to seconds
    df['start_sec'] = df['start_time'] / 1000.0
    df['end_sec'] = df['end_time'] / 1000.0
    df['duration_sec'] = df['end_sec'] - df['start_sec']
    
    # Map language labels
    lang_map = {
        'CS': 'CS',
        'EN': 'EN',
        'ZH': 'ZH'
    }
    df['lang'] = df['language'].map(lang_map).fillna('UNK')
    
    # Create condition labels
    def get_condition(lang):
        if lang == 'CS':
            return 'code_switched'
        elif lang == 'EN':
            return 'monolingual_EN'
        elif lang == 'ZH':
            return 'monolingual_ZH'
        else:
            return 'unknown'
    
    df['condition'] = df['lang'].apply(get_condition)
    
    # Filter out unknown language
    df = df[df['lang'] != 'UNK']
    
    # Build manifest rows
    print("\nBuilding manifest rows...")
    rows = []
    wav_path = pathlib.Path(wav_dir)
    
    for _, row in df.iterrows():
        file_id = row['file']
        start_sec = row['start_sec']
        end_sec = row['end_sec']
        speaker = row['speaker']
        lang = row['lang']
        condition = row['condition']
        transcript = str(row.get('filtered_transcript_2015', row.get('transcript_2015', '')))
        
        # Build WAV path - SEAME files are already sliced in interview_aligned/interview_aligned/
        # Files use decimal seconds in filename: {file_id}_{start_sec}_{end_sec}.wav
        # But CSV has milliseconds, so convert to seconds for matching
        start_sec_str = f"{start_sec:.3f}".rstrip('0').rstrip('.')
        end_sec_str = f"{end_sec:.3f}".rstrip('0').rstrip('.')
        
        # Try exact match first
        wav_filename_exact = f"{file_id}_{start_sec_str}_{end_sec_str}.wav"
        wav_filename_ms = f"{file_id}_{int(row['start_time'])}_{int(row['end_time'])}.wav"
        
        # Check multiple possible locations and naming patterns
        wav_dir = wav_path / "interview_aligned" / "interview_aligned"
        if not wav_dir.exists():
            wav_dir = pathlib.Path("data/SEAME/interview_aligned/interview_aligned")
        
        wav_file = None
        # Try exact decimal match
        if wav_dir.exists():
            exact_path = wav_dir / wav_filename_exact
            if exact_path.exists():
                wav_file = str(exact_path)
            else:
                # Try integer milliseconds format
                ms_path = wav_dir / wav_filename_ms
                if ms_path.exists():
                    wav_file = str(ms_path)
                else:
                    # Try to find closest match by searching for files with same file_id
                    # and similar timestamps (within 0.1 seconds)
                    pattern = f"{file_id}_*.wav"
                    matches = list(wav_dir.glob(pattern))
                    if matches:
                        # Use first match (files are already sliced correctly)
                        wav_file = str(matches[0])
        
        # Create utterance ID
        utt_id = f"{file_id}_{start_sec:.3f}_{end_sec:.3f}"
        
        # Use found file or construct expected path
        if not wav_file:
            wav_dir = wav_path / "interview_aligned" / "interview_aligned"
            if not wav_dir.exists():
                wav_dir = pathlib.Path("data/SEAME/interview_aligned/interview_aligned")
            wav_file = str(wav_dir / wav_filename_exact)
        
        rows.append({
            'utt_id': utt_id,
            'file_id': file_id,
            'wav': wav_file,
            'start': start_sec,
            'end': end_sec,
            'speaker': speaker,
            'lang': lang,
            'condition': condition,
            'text': transcript,
            'duration_sec': row['duration_sec']
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
    
    # Check duration distribution
    print(f"\nDuration statistics:")
    print(f"  Mean: {manifest_df['duration_sec'].mean():.2f}s")
    print(f"  Median: {manifest_df['duration_sec'].median():.2f}s")
    print(f"  Min: {manifest_df['duration_sec'].min():.2f}s")
    print(f"  Max: {manifest_df['duration_sec'].max():.2f}s")
    
    return manifest_df

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Build SEAME manifest for prosody analysis')
    p.add_argument('--csv', type=str,
                   default='data/SEAME/SEAME_data_annotation_new_2015_annotated_4_17_24.csv',
                   help='SEAME CSV file')
    p.add_argument('--wav-dir', type=str,
                   default='data/SEAME',
                   help='Directory containing SEAME WAV files')
    p.add_argument('--output', type=str,
                   default='manifests/seame_manifest.csv',
                   help='Output manifest CSV')
    
    args = p.parse_args()
    
    csv_file = pathlib.Path(args.csv)
    wav_dir = pathlib.Path(args.wav_dir)
    output_file = pathlib.Path(args.output)
    
    if not csv_file.exists():
        print(f"ERROR: CSV file not found: {csv_file}")
        exit(1)
    
    if not wav_dir.exists():
        print(f"WARNING: WAV directory not found: {wav_dir}")
        print("  Manifest will be created but may have missing files")
    
    build_seame_manifest(csv_file, wav_dir, output_file)

