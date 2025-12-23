#!/usr/bin/env python3
"""
Validate manually annotated word-level language tags.

This script checks:
1. All words have valid language tags (EN, HI, OTHER)
2. Word counts match between transcript and tags
3. Consistency checks (e.g., monolingual utterances should have consistent tags)

Usage:
    python scripts/11_validate_word_annotations.py --input masac_words_for_annotation.csv
"""

import argparse
import pathlib
import pandas as pd
import re


def tokenize_transcript(text):
    """Tokenize transcript into words."""
    if pd.isna(text) or text == "":
        return []
    tokens = re.findall(r'\S+', str(text))
    words = []
    for token in tokens:
        word_parts = re.findall(r'\w+|[^\w\s]', token)
        words.extend(word_parts)
    return words


def validate_annotations(word_csv):
    """
    Validate manually annotated word-level tags.
    
    Args:
        word_csv: Path to annotated word-level CSV
    """
    print(f"Reading annotations from: {word_csv}")
    word_df = pd.read_csv(word_csv)
    
    print(f"Total word annotations: {len(word_df)}")
    print(f"Unique utterances: {word_df['utterance_idx'].nunique()}")
    
    # Valid language tags
    valid_tags = {'EN', 'HI', 'OTHER', 'UNK'}
    
    # Check 1: All tags are valid
    print("\n=== Validation Check 1: Valid Language Tags ===")
    invalid_tags = word_df[~word_df['language_tag'].isin(valid_tags)]
    if len(invalid_tags) > 0:
        print(f"WARNING: Found {len(invalid_tags)} words with invalid tags:")
        print(invalid_tags[['file_id', 'word', 'language_tag']].head(10))
    else:
        print("✓ All tags are valid (EN, HI, OTHER, or UNK)")
    
    # Check 2: Word counts match transcripts
    print("\n=== Validation Check 2: Word Count Alignment ===")
    mismatches = []
    
    for file_id in word_df['file_id'].unique():
        file_words = word_df[word_df['file_id'] == file_id]
        
        for utt_idx in file_words['utterance_idx'].unique():
            utt_words = file_words[file_words['utterance_idx'] == utt_idx]
            transcript = utt_words['transcript'].iloc[0]
            
            # Tokenize transcript
            expected_words = tokenize_transcript(transcript)
            annotated_words = utt_words['word'].tolist()
            
            if len(expected_words) != len(annotated_words):
                mismatches.append({
                    'file_id': file_id,
                    'utterance_idx': utt_idx,
                    'expected_count': len(expected_words),
                    'annotated_count': len(annotated_words),
                    'transcript': transcript[:50] + '...' if len(transcript) > 50 else transcript
                })
    
    if len(mismatches) > 0:
        print(f"WARNING: Found {len(mismatches)} utterances with word count mismatches:")
        mismatch_df = pd.DataFrame(mismatches)
        print(mismatch_df.head(10))
    else:
        print("✓ All word counts match transcripts")
    
    # Check 3: Consistency with utterance-level labels
    print("\n=== Validation Check 3: Consistency with Utterance Labels ===")
    
    for file_id in word_df['file_id'].unique():
        file_words = word_df[word_df['file_id'] == file_id]
        
        for utt_idx in file_words['utterance_idx'].unique():
            utt_words = file_words[file_words['utterance_idx'] == utt_idx]
            utterance_lang = utt_words['utterance_lang'].iloc[0]
            word_tags = utt_words['language_tag'].tolist()
            
            # Count languages in word tags
            unique_langs = set([t for t in word_tags if t in ['EN', 'HI']])
            n_languages = len(unique_langs)
            
            # Check consistency
            if utterance_lang == 'EN' and n_languages > 1:
                print(f"WARNING: {file_id} (utt {utt_idx}) marked as EN but has multiple languages")
            elif utterance_lang == 'HI' and n_languages > 1:
                print(f"WARNING: {file_id} (utt {utt_idx}) marked as HI but has multiple languages")
            elif utterance_lang == 'CSW' and n_languages <= 1:
                print(f"INFO: {file_id} (utt {utt_idx}) marked as CSW but has only one language")
    
    # Summary statistics
    print("\n=== Summary Statistics ===")
    tag_counts = word_df['language_tag'].value_counts()
    print("Language tag distribution:")
    for tag, count in tag_counts.items():
        pct = 100 * count / len(word_df)
        print(f"  {tag}: {count:,} ({pct:.1f}%)")
    
    # Count UNK tags (unannotated)
    unk_count = (word_df['language_tag'] == 'UNK').sum()
    if unk_count > 0:
        print(f"\nWARNING: {unk_count} words still marked as UNK (unannotated)")
    else:
        print("\n✓ All words have been annotated")
    
    print("\nValidation complete!")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Validate manually annotated word-level tags')
    p.add_argument('--input', type=str, required=True,
                   help='Input CSV file with manually annotated words')
    
    args = p.parse_args()
    
    input_file = pathlib.Path(args.input)
    
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        exit(1)
    
    validate_annotations(input_file)

