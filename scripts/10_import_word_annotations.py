#!/usr/bin/env python3
"""
Import manually annotated word-level language tags back into MaSaC format.

This script:
1. Reads the manually annotated word-level CSV
2. Groups words back by utterance
3. Updates the LID_tags column in the original CSV
4. Saves updated CSV with manual annotations

Usage:
    python scripts/10_import_word_annotations.py --input masac_words_for_annotation.csv --original masac_data_compiled.csv --output masac_data_compiled_manual.csv
"""

import argparse
import pathlib
import pandas as pd
import ast


def import_word_annotations(word_csv, original_csv, output_csv):
    """
    Import manually annotated word-level tags back into utterance-level format.
    
    Args:
        word_csv: Path to manually annotated word-level CSV
        original_csv: Path to original masac_data_compiled.csv
        output_csv: Path to save updated CSV with manual annotations
    """
    print(f"Reading word-level annotations from: {word_csv}")
    word_df = pd.read_csv(word_csv)
    
    print(f"Reading original MaSaC data from: {original_csv}")
    original_df = pd.read_csv(original_csv, low_memory=False)
    
    # Group words by utterance
    print("Grouping words by utterance...")
    
    # Create a mapping from (file_id, utterance_idx) to list of language tags
    utterance_tags = {}
    
    for _, row in word_df.iterrows():
        file_id = row['file_id']
        utterance_idx = row['utterance_idx']
        lang_tag = row['language_tag']
        
        key = (file_id, utterance_idx)
        if key not in utterance_tags:
            utterance_tags[key] = []
        
        utterance_tags[key].append(lang_tag)
    
    print(f"Found {len(utterance_tags)} utterances with annotations")
    
    # Update original DataFrame
    updated_rows = []
    updated_count = 0
    
    for idx, row in original_df.iterrows():
        file_id = row['name']
        key = (file_id, idx)
        
        if key in utterance_tags:
            # Update LID_tags with manual annotations
            new_tags = utterance_tags[key]
            row['LID_tags'] = str(new_tags)
            updated_count += 1
        # If no manual annotation found, keep original LID_tags
        
        updated_rows.append(row.to_dict())
    
    # Create updated DataFrame
    updated_df = pd.DataFrame(updated_rows)
    
    # Save updated CSV
    updated_df.to_csv(output_csv, index=False)
    print(f"\nSaved updated data to: {output_csv}")
    print(f"  - Total utterances: {len(updated_df)}")
    print(f"  - Updated with manual annotations: {updated_count}")
    
    # Show statistics
    if 'LID_tags' in updated_df.columns:
        # Count code-switched utterances (those with multiple languages)
        def count_languages(lid_str):
            if pd.isna(lid_str):
                return 0
            try:
                tags = ast.literal_eval(lid_str) if isinstance(lid_str, str) else lid_str
                unique_langs = set([t for t in tags if t in ['EN', 'HI']])
                return len(unique_langs)
            except:
                return 0
        
        updated_df['n_languages'] = updated_df['LID_tags'].apply(count_languages)
        csw_count = (updated_df['n_languages'] > 1).sum()
        print(f"  - Code-switched utterances (multiple languages): {csw_count}")
    
    return updated_df


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Import manually annotated word-level tags')
    p.add_argument('--input', type=str, required=True,
                   help='Input CSV file with manually annotated words')
    p.add_argument('--original', type=str,
                   default='data/masac_raw/masac_data_compiled.csv',
                   help='Original MaSaC CSV file')
    p.add_argument('--output', type=str,
                   default='data/masac_raw/masac_data_compiled_manual.csv',
                   help='Output CSV file with updated annotations')
    
    args = p.parse_args()
    
    input_file = pathlib.Path(args.input)
    original_file = pathlib.Path(args.original)
    output_file = pathlib.Path(args.output)
    
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        exit(1)
    
    if not original_file.exists():
        print(f"ERROR: Original file not found: {original_file}")
        exit(1)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    import_word_annotations(input_file, original_file, output_file)

