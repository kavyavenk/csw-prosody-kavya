"""
Data Exploration Script for SEAME and MASAC Corpora
Extracts key statistics and information about the data for pilot subset testing.
"""

import argparse
import pandas as pd
import pathlib
import numpy as np
from collections import Counter

p = argparse.ArgumentParser(description="Explore corpus data and extract statistics")
p.add_argument("--corpus", choices=["masac", "seame"], required=True)
p.add_argument("--output", type=str, default=None, help="Output CSV file for statistics")
args = p.parse_args()

RAW = pathlib.Path(f"data/{args.corpus}_raw")
OUT_DIR = pathlib.Path("reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"\n{'='*60}")
print(f"Exploring {args.corpus.upper()} Corpus")
print(f"{'='*60}\n")

stats = {}

if args.corpus == "seame":
    # SEAME data exploration
    # SEAME data is in data/SEAME/ not data/seame_raw/
    csv_file = pathlib.Path("data/SEAME/SEAME_data_annotation_new_2015_annotated_4_17_24.csv")
    if not csv_file.exists():
        print(f"ERROR: SEAME CSV not found at {csv_file}")
        exit(1)
    
    print(f"Reading SEAME data from: {csv_file}")
    df = pd.read_csv(csv_file, low_memory=False)
    
    print(f"Total rows: {len(df)}")
    stats['total_utterances'] = len(df)
    
    # Language distribution
    if 'language' in df.columns:
        lang_counts = df['language'].value_counts()
        print(f"\nLanguage Distribution:")
        for lang, count in lang_counts.items():
            pct = 100 * count / len(df)
            print(f"  {lang}: {count:,} ({pct:.1f}%)")
        stats['language_distribution'] = lang_counts.to_dict()
    
    # Speaker information
    if 'speaker' in df.columns:
        n_speakers = df['speaker'].nunique()
        print(f"\nNumber of unique speakers: {n_speakers}")
        stats['n_speakers'] = n_speakers
        
        # Speakers by language
        if 'language' in df.columns:
            speaker_lang = df.groupby(['speaker', 'language']).size().reset_index(name='count')
            print(f"\nSpeakers producing each language type:")
            for lang in df['language'].unique():
                speakers = speaker_lang[speaker_lang['language'] == lang]['speaker'].nunique()
                print(f"  {lang}: {speakers} speakers")
    
    # Duration information
    if 'start_time' in df.columns and 'end_time' in df.columns:
        df['duration_ms'] = df['end_time'] - df['start_time']
        df['duration_sec'] = df['duration_ms'] / 1000.0
        
        print(f"\nDuration Statistics (seconds):")
        print(f"  Mean: {df['duration_sec'].mean():.2f}")
        print(f"  Median: {df['duration_sec'].median():.2f}")
        print(f"  Min: {df['duration_sec'].min():.2f}")
        print(f"  Max: {df['duration_sec'].max():.2f}")
        print(f"  Total duration: {df['duration_sec'].sum() / 3600:.2f} hours")
        
        stats['duration_mean_sec'] = df['duration_sec'].mean()
        stats['duration_median_sec'] = df['duration_sec'].median()
        stats['total_hours'] = df['duration_sec'].sum() / 3600
        
        # Duration by language
        if 'language' in df.columns:
            print(f"\nDuration by Language (seconds):")
            for lang in df['language'].unique():
                lang_df = df[df['language'] == lang]
                print(f"  {lang}: mean={lang_df['duration_sec'].mean():.2f}, "
                      f"median={lang_df['duration_sec'].median():.2f}")
    
    # File information
    if 'file' in df.columns:
        n_files = df['file'].nunique()
        print(f"\nNumber of unique audio files: {n_files}")
        stats['n_files'] = n_files
    
    # Conversation information
    if 'conversation' in df.columns:
        n_convos = df['conversation'].nunique()
        print(f"\nNumber of conversations: {n_convos}")
        stats['n_conversations'] = n_convos
    
    # Demographic information
    if 'gender' in df.columns:
        gender_counts = df['gender'].value_counts()
        print(f"\nGender Distribution:")
        for g, count in gender_counts.items():
            print(f"  {g}: {count:,}")
        stats['gender_distribution'] = gender_counts.to_dict()
    
    if 'age' in df.columns:
        print(f"\nAge Statistics:")
        print(f"  Mean: {df['age'].mean():.1f}")
        print(f"  Median: {df['age'].median():.1f}")
        print(f"  Range: {df['age'].min():.0f} - {df['age'].max():.0f}")
        stats['age_mean'] = df['age'].mean()
        stats['age_range'] = (df['age'].min(), df['age'].max())
    
    # Code-switching information
    if 'number_of_code_switches' in df.columns:
        cs_rows = df[df['number_of_code_switches'] > 0]
        print(f"\nCode-Switching Statistics:")
        print(f"  Utterances with CS: {len(cs_rows):,} ({100*len(cs_rows)/len(df):.1f}%)")
        print(f"  Mean switches per CS utterance: {cs_rows['number_of_code_switches'].mean():.2f}")
        stats['cs_utterances'] = len(cs_rows)
        stats['cs_percentage'] = 100*len(cs_rows)/len(df)
    
    # Sample data preview
    print(f"\nSample Data (first 5 rows):")
    print(df[['file', 'speaker', 'start_time', 'end_time', 'language']].head())
    
    # Save detailed statistics
    out_file = OUT_DIR / f"{args.corpus}_exploration.csv"
    df.to_csv(out_file, index=False)
    print(f"\nSaved full data to: {out_file}")

elif args.corpus == "masac":
    # MASAC data exploration
    csv_file = RAW / "masac_data_compiled.csv"
    if not csv_file.exists():
        print(f"ERROR: MASAC CSV not found at {csv_file}")
        exit(1)
    
    print(f"Reading MASAC data from: {csv_file}")
    df = pd.read_csv(csv_file, low_memory=False)
    
    print(f"Total rows: {len(df)}")
    stats['total_utterances'] = len(df)
    
    # Language distribution
    if 'Language' in df.columns:
        lang_counts = df['Language'].value_counts()
        print(f"\nLanguage Distribution:")
        for lang, count in lang_counts.items():
            pct = 100 * count / len(df)
            print(f"  {lang}: {count:,} ({pct:.1f}%)")
        stats['language_distribution'] = lang_counts.to_dict()
    
    # Extract language from LID_tags if available
    if 'LID_tags' in df.columns:
        print(f"\nAnalyzing LID tags...")
        # Count CSW utterances (those with multiple languages)
        def count_languages(lid_str):
            if pd.isna(lid_str):
                return 0
            try:
                # Parse the string representation of list
                import ast
                tags = ast.literal_eval(lid_str) if isinstance(lid_str, str) else lid_str
                unique_langs = set([t for t in tags if t in ['EN', 'HI', 'CS']])
                return len(unique_langs)
            except:
                return 0
        
        df['n_languages_in_utt'] = df['LID_tags'].apply(count_languages)
        csw_from_tags = (df['n_languages_in_utt'] > 1).sum()
        print(f"  Utterances with multiple languages (from tags): {csw_from_tags:,}")
    
    # Transcript length analysis
    if 'Transcript' in df.columns:
        df['transcript_length'] = df['Transcript'].str.len()
        df['n_words'] = df['Transcript'].str.split().str.len()
        
        print(f"\nTranscript Statistics:")
        print(f"  Mean characters: {df['transcript_length'].mean():.1f}")
        print(f"  Mean words: {df['n_words'].mean():.1f}")
        stats['mean_words'] = df['n_words'].mean()
    
    # File information
    if 'name' in df.columns:
        n_files = df['name'].nunique()
        print(f"\nNumber of unique audio files: {n_files}")
        stats['n_files'] = n_files
        
        # Check if audio files exist
        wav_dir = pathlib.Path("data/masac_wav16k")
        if wav_dir.exists():
            existing_wavs = set([f.stem for f in wav_dir.rglob("*.wav")])
            df['wav_exists'] = df['name'].str.replace('.wav', '').isin(existing_wavs)
            n_existing = df['wav_exists'].sum()
            print(f"  Audio files available: {n_existing}/{n_files} ({100*n_existing/n_files:.1f}%)")
            stats['audio_files_available'] = n_existing
    
    # Sample data preview
    print(f"\nSample Data (first 5 rows):")
    display_cols = ['name', 'Language']
    if 'Transcript' in df.columns:
        display_cols.append('Transcript')
    if 'LID_tags' in df.columns:
        display_cols.append('LID_tags')
    print(df[display_cols].head())
    
    # Save detailed statistics
    out_file = OUT_DIR / f"{args.corpus}_exploration.csv"
    df.to_csv(out_file, index=False)
    print(f"\nSaved full data to: {out_file}")

# Save summary statistics
summary_file = OUT_DIR / f"{args.corpus}_summary_stats.txt"
with open(summary_file, 'w') as f:
    f.write(f"{args.corpus.upper()} Corpus Summary Statistics\n")
    f.write("="*60 + "\n\n")
    for key, value in stats.items():
        f.write(f"{key}: {value}\n")
print(f"\nSaved summary to: {summary_file}")

print(f"\n{'='*60}")
print("Exploration complete!")
print(f"{'='*60}\n")

