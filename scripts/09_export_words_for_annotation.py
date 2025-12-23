#!/usr/bin/env python3
"""
Export word-level data from MaSaC corpus for manual language annotation.

This script:
1. Reads the MaSaC compiled CSV
2. Tokenizes transcripts into words
3. Aligns words with existing LID_tags (if available)
4. Exports to a CSV format suitable for manual editing

Usage:
    python scripts/09_export_words_for_annotation.py [--output OUTPUT_FILE] [--subset N]
"""

import argparse
import ast
import pathlib
import pandas as pd
import re


def tokenize_transcript(text):
    """
    Tokenize transcript into words, preserving punctuation as separate tokens.
    This matches the format used in LID_tags.
    """
    if pd.isna(text) or text == "":
        return []
    
    # Split on whitespace and punctuation, keeping punctuation as separate tokens
    # This pattern splits on whitespace and captures punctuation separately
    tokens = re.findall(r'\S+', str(text))
    words = []
    for token in tokens:
        # Split punctuation from words (e.g., "word!" -> ["word", "!"])
        word_parts = re.findall(r'\w+|[^\w\s]', token)
        words.extend(word_parts)
    
    return words


def parse_lid_tags(lid_str):
    """Parse LID_tags string representation of list into actual list."""
    if pd.isna(lid_str):
        return []
    try:
        if isinstance(lid_str, str):
            return ast.literal_eval(lid_str)
        return lid_str
    except:
        return []


def export_words_for_annotation(csv_file, output_file, subset=None):
    """
    Export word-level data for manual annotation.
    
    Args:
        csv_file: Path to masac_data_compiled.csv
        output_file: Path to output CSV for manual editing
        subset: Optional number of utterances to process (for testing)
    """
    print(f"Reading MaSaC data from: {csv_file}")
    df = pd.read_csv(csv_file, low_memory=False)
    
    if subset:
        df = df.head(subset)
        print(f"Processing subset of {subset} utterances")
    
    print(f"Total utterances: {len(df)}")
    
    # Prepare word-level data
    word_rows = []
    
    for idx, row in df.iterrows():
        file_id = row['name']
        transcript = row.get('Transcript', '')
        lid_tags = row.get('LID_tags', [])
        utterance_lang = row.get('Language', 'UNK')
        
        # Tokenize transcript
        words = tokenize_transcript(transcript)
        
        # Parse existing LID tags
        existing_tags = parse_lid_tags(lid_tags)
        
        # Align words with tags
        # If we have existing tags, use them; otherwise mark as UNK
        for word_idx, word in enumerate(words):
            if word_idx < len(existing_tags):
                lang_tag = existing_tags[word_idx]
            else:
                lang_tag = 'UNK'  # Unknown if no tag available
            
            word_rows.append({
                'file_id': file_id,
                'utterance_idx': idx,
                'word_idx': word_idx,
                'word': word,
                'language_tag': lang_tag,  # EN, HI, OTHER, or UNK
                'utterance_lang': utterance_lang,  # CSW, EN, HI
                'transcript': transcript,  # Full transcript for context
            })
    
    # Create DataFrame
    word_df = pd.DataFrame(word_rows)
    
    # Save to CSV
    word_df.to_csv(output_file, index=False)
    print(f"\nExported {len(word_df)} words to: {output_file}")
    print(f"  - Files: {word_df['file_id'].nunique()}")
    print(f"  - Utterances: {word_df['utterance_idx'].nunique()}")
    
    # Show language tag distribution
    if 'language_tag' in word_df.columns:
        tag_counts = word_df['language_tag'].value_counts()
        print(f"\nLanguage tag distribution:")
        for tag, count in tag_counts.items():
            pct = 100 * count / len(word_df)
            print(f"  {tag}: {count:,} ({pct:.1f}%)")
    
    print(f"\nTo manually annotate:")
    print(f"  1. Open {output_file} in Excel or a text editor")
    print(f"  2. Edit the 'language_tag' column (use EN, HI, or OTHER)")
    print(f"  3. Save the file")
    print(f"  4. Run: python scripts/10_import_word_annotations.py --input {output_file}")
    
    return word_df


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Export word-level data for manual annotation')
    p.add_argument('--input', type=str, 
                   default='data/masac_raw/masac_data_compiled.csv',
                   help='Input MaSaC CSV file')
    p.add_argument('--output', type=str,
                   default='data/masac_raw/masac_words_for_annotation.csv',
                   help='Output CSV file for manual editing')
    p.add_argument('--subset', type=int, default=None,
                   help='Process only first N utterances (for testing)')
    
    args = p.parse_args()
    
    input_file = pathlib.Path(args.input)
    output_file = pathlib.Path(args.output)
    
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        exit(1)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    export_words_for_annotation(input_file, output_file, args.subset)

