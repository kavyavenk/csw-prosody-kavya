#!/usr/bin/env python3
"""
Extract code-switch directionality (EN→ZH vs ZH→EN, EN→HI vs HI→EN).

This script analyzes word-level language tags to determine:
1. Switch direction (L1→L2 vs L2→L1)
2. Switch position in utterance
3. Number of switches per utterance
4. Switch type (insertional vs alternational)
"""

import argparse
import pathlib
import pandas as pd
import ast
from typing import List, Tuple, Optional

def extract_directionality_from_lid_tags(lid_tags: List[str], 
                                          l1_lang: str = 'ZH') -> dict:
    """
    Extract switch directionality from LID tags.
    
    Args:
        lid_tags: List of language tags (EN, ZH, HI, OTHER)
        l1_lang: Primary language (ZH for SEAME, HI for MASAC)
    
    Returns dict with:
        - switch_directions: list of switch directions (e.g., ['EN→ZH', 'ZH→EN'])
        - n_switches: number of switches
        - first_switch_direction: direction of first switch
        - switch_type: 'insertional' or 'alternational'
        - switch_positions: list of switch positions
    """
    if not lid_tags or len(lid_tags) < 2:
        return {
            'switch_directions': [],
            'n_switches': 0,
            'first_switch_direction': None,
            'switch_type': None,
            'switch_positions': []
        }
    
    # Filter out OTHER tags for switch detection
    lang_tags = [tag for tag in lid_tags if tag in ['EN', 'ZH', 'HI']]
    
    if len(set(lang_tags)) < 2:
        # No code-switching detected
        return {
            'switch_directions': [],
            'n_switches': 0,
            'first_switch_direction': None,
            'switch_type': None,
            'switch_positions': []
        }
    
    # Find switch positions
    switch_directions = []
    switch_positions = []
    prev_tag = None
    
    for i, tag in enumerate(lang_tags):
        if prev_tag and tag != prev_tag:
            direction = f"{prev_tag}→{tag}"
            switch_directions.append(direction)
            switch_positions.append(i)
        prev_tag = tag
    
    # Determine switch type
    # Insertional: one language dominates, other appears in short segments
    # Alternational: languages alternate more evenly
    if len(switch_directions) == 0:
        switch_type = None
    elif len(switch_directions) <= 2:
        # Simple case: likely insertional
        switch_type = 'insertional'
    else:
        # Multiple switches: check if alternating pattern
        unique_dirs = set(switch_directions)
        if len(unique_dirs) == 1:
            # All switches in same direction: insertional
            switch_type = 'insertional'
        else:
            # Mixed directions: alternational
            switch_type = 'alternational'
    
    first_switch_direction = switch_directions[0] if switch_directions else None
    
    return {
        'switch_directions': switch_directions,
        'n_switches': len(switch_directions),
        'first_switch_direction': first_switch_direction,
        'switch_type': switch_type,
        'switch_positions': switch_positions
    }

def classify_switch_direction(switch_dir: str, l1_lang: str) -> str:
    """
    Classify switch direction as L1→L2 or L2→L1.
    
    Args:
        switch_dir: Switch direction string (e.g., 'EN→ZH')
        l1_lang: Primary language (ZH or HI)
    
    Returns: 'L1→L2', 'L2→L1', or None
    """
    if not switch_dir:
        return None
    
    parts = switch_dir.split('→')
    if len(parts) != 2:
        return None
    
    from_lang, to_lang = parts
    
    if from_lang == l1_lang:
        return 'L1→L2'
    elif to_lang == l1_lang:
        return 'L2→L1'
    else:
        # Both are L2 (e.g., EN→EN, shouldn't happen but handle it)
        return None

def process_manifest_with_words(manifest_file: str, word_file: Optional[str],
                                output_file: str, corpus: str):
    """
    Process manifest to add switch directionality information.
    
    For MASAC: uses word-level CSV if available
    For SEAME: may need to parse LID tags from manifest or separate file
    """
    print(f"Reading manifest from: {manifest_file}")
    df = pd.read_csv(manifest_file, low_memory=False)
    
    print(f"Total utterances: {len(df)}")
    
    # Determine L1 language
    l1_lang = 'ZH' if corpus == 'seame' else 'HI'
    
    # Initialize new columns
    df['switch_direction'] = None
    df['first_switch_direction'] = None
    df['n_switches'] = 0
    df['switch_type'] = None
    df['switch_direction_class'] = None  # L1→L2 or L2→L1
    
    # Try to load word-level data if available
    word_df = None
    if word_file and pathlib.Path(word_file).exists():
        print(f"Loading word-level data from: {word_file}")
        word_df = pd.read_csv(word_file, low_memory=False)
        print(f"  Loaded {len(word_df)} word-level annotations")
        # Create lookup: file_id -> list of language tags
        word_lookup = {}
        for _, wrow in word_df.iterrows():
            file_id = str(wrow.get('file_id', '')).replace('.wav', '')
            if file_id not in word_lookup:
                word_lookup[file_id] = []
            lang_tag = wrow.get('language_tag', 'OTHER')
            if lang_tag in ['EN', 'HI', 'ZH']:
                word_lookup[file_id].append(lang_tag)
    
    # For MASAC, try loading LID_tags from raw CSV
    raw_lid_lookup = {}
    if corpus == 'masac':
        raw_csv = pathlib.Path('data/masac_raw/masac_data_compiled.csv')
        if raw_csv.exists():
            print(f"Loading LID tags from raw MASAC CSV: {raw_csv}")
            try:
                raw_df = pd.read_csv(raw_csv, low_memory=False)
                for _, rrow in raw_df.iterrows():
                    file_name = str(rrow.get('name', ''))
                    file_id = file_name.replace('.wav', '')
                    lid_tags_str = rrow.get('LID_tags', '')
                    if pd.notna(lid_tags_str) and lid_tags_str:
                        try:
                            lid_tags = ast.literal_eval(str(lid_tags_str))
                            raw_lid_lookup[file_id] = lid_tags
                        except:
                            pass
                print(f"  Loaded LID tags for {len(raw_lid_lookup)} utterances")
            except Exception as e:
                print(f"  Warning: Could not load raw CSV: {e}")
    
    print("\nProcessing utterances...")
    processed = 0
    
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  Processed {idx}/{len(df)} utterances...")
        
        lang = row.get('lang', '')
        if lang != 'CS':
            continue
        
        lid_tags = None
        
        # Try to get LID tags from various sources
        if 'LID_tags' in row:
            try:
                lid_tags_str = str(row['LID_tags'])
                if lid_tags_str and lid_tags_str != 'nan':
                    lid_tags = ast.literal_eval(lid_tags_str)
            except:
                pass
        
        # If not in manifest, try raw CSV lookup (for MASAC)
        if not lid_tags and corpus == 'masac':
            file_id = str(row.get('file_id', '')).replace('.wav', '')
            if file_id in raw_lid_lookup:
                lid_tags = raw_lid_lookup[file_id]
        
        # If still not found, try word-level file
        if not lid_tags and word_df is not None:
            file_id = str(row.get('file_id', '')).replace('.wav', '')
            if file_id in word_lookup:
                lid_tags = word_lookup[file_id]
        
        if not lid_tags:
            continue
        
        # Extract directionality
        dir_info = extract_directionality_from_lid_tags(lid_tags, l1_lang)
        
        df.at[idx, 'n_switches'] = dir_info['n_switches']
        df.at[idx, 'switch_type'] = dir_info['switch_type']
        df.at[idx, 'first_switch_direction'] = dir_info['first_switch_direction']
        
        if dir_info['switch_directions']:
            df.at[idx, 'switch_direction'] = ','.join(dir_info['switch_directions'])
            
            # Classify first switch
            first_dir = dir_info['first_switch_direction']
            if first_dir:
                direction_class = classify_switch_direction(first_dir, l1_lang)
                df.at[idx, 'switch_direction_class'] = direction_class
        
        processed += 1
    
    print(f"\nProcessed {processed} CSW utterances")
    
    # Save output
    output_path = pathlib.Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"\nSaved annotated manifest to: {output_file}")
    
    # Print statistics
    cs_df = df[df['lang'] == 'CS']
    if len(cs_df) > 0:
        print("\n=== Switch Directionality Statistics ===")
        print(f"CSW utterances with direction info: {cs_df['switch_direction'].notna().sum()}")
        print(f"Average switches per CSW utterance: {cs_df['n_switches'].mean():.2f}")
        
        if cs_df['switch_direction_class'].notna().any():
            print("\nSwitch direction distribution:")
            dir_counts = cs_df['switch_direction_class'].value_counts()
            for dir_class, count in dir_counts.items():
                pct = 100 * count / len(cs_df[cs_df['switch_direction_class'].notna()])
                print(f"  {dir_class}: {count} ({pct:.1f}%)")
        
        if cs_df['switch_type'].notna().any():
            print("\nSwitch type distribution:")
            type_counts = cs_df['switch_type'].value_counts()
            for switch_type, count in type_counts.items():
                pct = 100 * count / len(cs_df[cs_df['switch_type'].notna()])
                print(f"  {switch_type}: {count} ({pct:.1f}%)")
    
    return df

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Extract code-switch directionality from LID tags'
    )
    p.add_argument('--manifest', type=str, required=True,
                   help='Input manifest CSV file')
    p.add_argument('--words', type=str, default=None,
                   help='Optional word-level CSV with LID tags')
    p.add_argument('--output', type=str, required=True,
                   help='Output manifest CSV with directionality')
    p.add_argument('--corpus', type=str, choices=['seame', 'masac'],
                   default='seame', help='Corpus name')
    
    args = p.parse_args()
    
    manifest_file = pathlib.Path(args.manifest)
    if not manifest_file.exists():
        print(f"ERROR: Manifest file not found: {manifest_file}")
        exit(1)
    
    process_manifest_with_words(
        str(manifest_file), args.words, args.output, args.corpus
    )
