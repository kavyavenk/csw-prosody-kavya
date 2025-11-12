"""
Pilot Subset Selection for SEAME and MASAC Corpora

Selects balanced subsets for initial testing, ensuring:
- Equal representation across conditions (CS, monolingual_EN, monolingual_ZH/HI)
- Speaker balance
- Audio file availability
- Minimum utterance duration requirements
"""

import argparse
import pandas as pd
import pathlib
import numpy as np
from collections import Counter

p = argparse.ArgumentParser(description="Select pilot subsets for prosody analysis")
p.add_argument("--corpus", choices=["masac", "seame"], required=True)
p.add_argument("--n_per_condition", type=int, default=100, 
               help="Number of utterances per condition (default: 100)")
p.add_argument("--min_duration_sec", type=float, default=0.5,
               help="Minimum utterance duration in seconds (default: 0.5)")
p.add_argument("--max_duration_sec", type=float, default=10.0,
               help="Maximum utterance duration in seconds (default: 10.0)")
p.add_argument("--output", type=str, default=None,
               help="Output manifest file (default: manifests/{corpus}_pilot_manifest.csv)")
args = p.parse_args()

RAW = pathlib.Path(f"data/{args.corpus}_raw")
WAV = pathlib.Path(f"data/{args.corpus}_wav16k")
OUT_DIR = pathlib.Path("manifests")
OUT_DIR.mkdir(parents=True, exist_ok=True)

if args.output:
    OUT_FILE = pathlib.Path(args.output)
else:
    OUT_FILE = OUT_DIR / f"{args.corpus}_pilot_manifest.csv"

print(f"\n{'='*60}")
print(f"Pilot Subset Selection: {args.corpus.upper()}")
print(f"{'='*60}\n")
print(f"Target: {args.n_per_condition} utterances per condition")
print(f"Duration range: {args.min_duration_sec:.1f}s - {args.max_duration_sec:.1f}s\n")

# Load existing manifest if available
MANIFEST_FILE = OUT_DIR / f"{args.corpus}_manifest.csv"
if MANIFEST_FILE.exists():
    print(f"Loading existing manifest: {MANIFEST_FILE}")
    df = pd.read_csv(MANIFEST_FILE)
else:
    print(f"Building manifest from raw data...")
    
    if args.corpus == "seame":
        # Load SEAME CSV
        csv_file = RAW / "SEAME_data_annotation_new_2015_annotated_4_17_24.csv"
        if not csv_file.exists():
            raise FileNotFoundError(f"SEAME CSV not found: {csv_file}")
        
        df_raw = pd.read_csv(csv_file, low_memory=False)
        
        # Convert time columns (milliseconds to seconds)
        df_raw['start_sec'] = df_raw['start_time'] / 1000.0
        df_raw['end_sec'] = df_raw['end_time'] / 1000.0
        df_raw['duration_sec'] = df_raw['end_sec'] - df_raw['start_sec']
        
        # Map language labels
        lang_map = {
            'CS': 'CS',
            'EN': 'EN',
            'ZH': 'ZH'
        }
        df_raw['lang'] = df_raw['language'].map(lang_map).fillna('UNK')
        
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
        
        df_raw['condition'] = df_raw['lang'].apply(get_condition)
        
        # Build manifest rows
        rows = []
        for _, row in df_raw.iterrows():
            if row['lang'] == 'UNK':
                continue
            
            file_id = row['file'].replace('.wav', '').replace('.TextGrid', '')
            wav_path = (WAV / f"{row['file']}").as_posix() if WAV.exists() else ""
            
            rows.append({
                'utt_id': f"{file_id}_{row['start_sec']:.3f}_{row['end_sec']:.3f}",
                'file_id': file_id,
                'wav': wav_path,
                'start': row['start_sec'],
                'end': row['end_sec'],
                'speaker': row.get('speaker', 'unknown'),
                'lang': row['lang'],
                'condition': row['condition'],
                'text': str(row.get('transcript_2015', row.get('transcript_2014', ''))),
                'duration_sec': row['duration_sec']
            })
        
        df = pd.DataFrame(rows)
    
    elif args.corpus == "masac":
        # For MASAC, we need to check if timestamps are available
        # If not, we'll use individual utterance files
        csv_file = RAW / "masac_data_compiled.csv"
        if not csv_file.exists():
            raise FileNotFoundError(f"MASAC CSV not found: {csv_file}")
        
        df_raw = pd.read_csv(csv_file, low_memory=False)
        
        # Map language labels
        lang_map = {
            'CSW': 'CS',
            'EN': 'EN',
            'HI': 'HI'
        }
        df_raw['lang'] = df_raw['Language'].map(lang_map).fillna('UNK')
        
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
        
        df_raw['condition'] = df_raw['lang'].apply(get_condition)
        
        # Build manifest rows - MASAC files are individual utterances
        rows = []
        for _, row in df_raw.iterrows():
            if row['lang'] == 'UNK':
                continue
            
            file_id = row['name'].replace('.wav', '')
            wav_path = (WAV / row['name']).as_posix() if WAV.exists() else ""
            
            # For MASAC, each file is a separate utterance, so start=0, end=file_duration
            # We'll estimate duration later or use audio file duration
            rows.append({
                'utt_id': file_id,
                'file_id': file_id,
                'wav': wav_path,
                'start': 0.0,  # Will need to get from audio file
                'end': -1.0,   # Will need to get from audio file
                'speaker': 'unknown',  # MASAC may have speaker info elsewhere
                'lang': row['lang'],
                'condition': row['condition'],
                'text': str(row.get('Transcript', '')),
                'duration_sec': -1.0  # Will need to compute
            })
        
        df = pd.DataFrame(rows)

# Filter by duration if available
if 'duration_sec' in df.columns:
    before = len(df)
    df = df[
        (df['duration_sec'] >= args.min_duration_sec) & 
        (df['duration_sec'] <= args.max_duration_sec)
    ]
    print(f"Duration filter: {before} -> {len(df)} utterances")

# Check audio file availability
if WAV.exists():
    existing_files = set([f.stem for f in WAV.rglob("*.wav")])
    df['has_audio'] = df['file_id'].isin(existing_files)
    n_with_audio = df['has_audio'].sum()
    print(f"Audio files available: {n_with_audio}/{len(df)} ({100*n_with_audio/len(df):.1f}%)")
    df = df[df['has_audio']]
else:
    print(f"Warning: Audio directory not found: {WAV}")

# Select balanced subset
print(f"\nSelecting balanced subset...")
conditions = ['code_switched', 'monolingual_EN']
if args.corpus == "seame":
    conditions.append('monolingual_ZH')
else:
    conditions.append('monolingual_HI')

selected_rows = []
speaker_counts = Counter()

for condition in conditions:
    cond_df = df[df['condition'] == condition].copy()
    
    if len(cond_df) < args.n_per_condition:
        print(f"Warning: Only {len(cond_df)} utterances available for {condition} (need {args.n_per_condition})")
        n_select = len(cond_df)
    else:
        n_select = args.n_per_condition
    
    # Try to balance speakers
    if 'speaker' in cond_df.columns and cond_df['speaker'].nunique() > 1:
        # Group by speaker and sample proportionally
        speakers = cond_df['speaker'].unique()
        n_per_speaker = max(1, n_select // len(speakers))
        remainder = n_select % len(speakers)
        
        selected = []
        for i, speaker in enumerate(speakers):
            speaker_df = cond_df[cond_df['speaker'] == speaker]
            n_to_select = n_per_speaker + (1 if i < remainder else 0)
            if len(speaker_df) >= n_to_select:
                selected.append(speaker_df.sample(n=n_to_select, random_state=42))
        
        if selected:
            cond_selected = pd.concat(selected, ignore_index=True)
            if len(cond_selected) < n_select:
                # Fill remaining slots randomly
                remaining = cond_df[~cond_df.index.isin(cond_selected.index)]
                if len(remaining) > 0:
                    n_needed = n_select - len(cond_selected)
                    cond_selected = pd.concat([
                        cond_selected,
                        remaining.sample(n=min(n_needed, len(remaining)), random_state=42)
                    ], ignore_index=True)
        else:
            cond_selected = cond_df.sample(n=n_select, random_state=42)
    else:
        cond_selected = cond_df.sample(n=n_select, random_state=42)
    
    selected_rows.append(cond_selected)
    print(f"  {condition}: {len(cond_selected)} utterances")

df_pilot = pd.concat(selected_rows, ignore_index=True)

# Print statistics
print(f"\n{'='*60}")
print("Pilot Subset Statistics")
print(f"{'='*60}\n")
print(f"Total utterances: {len(df_pilot)}")
print(f"\nCondition distribution:")
print(df_pilot['condition'].value_counts())
print(f"\nSpeaker distribution:")
if 'speaker' in df_pilot.columns:
    print(df_pilot['speaker'].value_counts().head(10))
    print(f"  (Total unique speakers: {df_pilot['speaker'].nunique()})")

# Save pilot manifest
df_pilot = df_pilot.drop(columns=['has_audio'], errors='ignore')
df_pilot.to_csv(OUT_FILE, index=False)
print(f"\nSaved pilot manifest to: {OUT_FILE}")

print(f"\n{'='*60}")
print("Pilot subset selection complete!")
print(f"{'='*60}\n")

