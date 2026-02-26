#!/usr/bin/env python3
"""
Detect discourse markers and repetitions in CSW utterances.

This script identifies:
1. Discourse markers (like, you know, so, I mean, etc.) in English/Mandarin/Hindi
2. Word repetitions (exact and near-repetitions)
3. Proximity to code-switch boundaries

Output: Adds columns to manifest/features for downstream analysis.
"""

import argparse
import pathlib
import pandas as pd
import re
from typing import List, Tuple, Set

# Discourse markers by language
DISCOURSE_MARKERS = {
    'EN': {
        'fillers': ['um', 'uh', 'er', 'ah', 'eh'],
        'connectors': ['like', 'you know', 'i mean', 'so', 'well', 'actually', 
                      'basically', 'literally', 'right', 'okay', 'ok'],
        'reformulation': ['i mean', 'like', 'you know', 'sort of', 'kind of'],
        'emphasis': ['really', 'actually', 'literally', 'basically']
    },
    'ZH': {
        'fillers': ['呃', '嗯', '啊', '那个', '这个'],
        'connectors': ['然后', '所以', '但是', '可是', '不过', '而且', '而且', '就是'],
        'reformulation': ['就是', '那个', '这个'],
        'emphasis': ['真的', '其实', '就是']
    },
    'HI': {
        'fillers': ['um', 'uh', 'er', 'ah', 'eh', 'hmm'],
        'connectors': ['toh', 'phir', 'lekin', 'par', 'aur', 'ya', 'ki'],
        'reformulation': ['matlab', 'yani', 'jaise'],
        'emphasis': ['bilkul', 'sach mein', 'asli mein']
    }
}

def tokenize_text(text: str, lang: str = 'EN') -> List[str]:
    """Tokenize text into words, handling multilingual text."""
    if pd.isna(text) or text == '':
        return []
    
    # Handle list-like strings from CSV
    if isinstance(text, str) and text.startswith('['):
        # Try to parse as list
        try:
            import ast
            text_list = ast.literal_eval(text)
            if isinstance(text_list, list):
                text = ' '.join(str(t) for t in text_list)
        except:
            pass
    
    text = str(text).strip()
    if not text:
        return []
    
    # Simple tokenization - split on whitespace and punctuation
    # For Chinese, characters are already separated
    if lang == 'ZH':
        # Chinese characters are typically space-separated in transcripts
        tokens = re.findall(r'\S+', text)
    else:
        # For English/Hindi, split on whitespace
        tokens = re.findall(r'\S+', text.lower())
    
    return tokens

def detect_discourse_markers(tokens: List[str], lang: str) -> dict:
    """
    Detect discourse markers in tokenized text.
    
    Returns dict with:
    - has_discourse_marker: bool
    - discourse_marker_type: str (filler/connector/reformulation/emphasis)
    - discourse_marker_words: list of detected markers
    - n_discourse_markers: int
    """
    if lang not in DISCOURSE_MARKERS:
        lang = 'EN'  # Default to English
    
    markers = DISCOURSE_MARKERS[lang]
    detected = []
    types = []
    
    # Check for multi-word markers first
    text_lower = ' '.join(tokens).lower()
    
    for marker_type, marker_list in markers.items():
        for marker in marker_list:
            marker_lower = marker.lower()
            # Check if marker appears in text
            if marker_lower in text_lower:
                detected.append(marker)
                types.append(marker_type)
    
    return {
        'has_discourse_marker': len(detected) > 0,
        'discourse_marker_type': types[0] if types else None,
        'discourse_marker_words': detected,
        'n_discourse_markers': len(detected)
    }

def detect_repetitions(tokens: List[str], window: int = 3) -> dict:
    """
    Detect word repetitions within a window.
    
    Args:
        tokens: List of tokenized words
        window: Window size for detecting repetitions (default: 3)
    
    Returns dict with:
        - has_repetition: bool
        - repetition_words: list of repeated words
        - n_repetitions: int
        - repetition_positions: list of (word, position) tuples
    """
    if len(tokens) < 2:
        return {
            'has_repetition': False,
            'repetition_words': [],
            'n_repetitions': 0,
            'repetition_positions': []
        }
    
    repetitions = []
    positions = []
    
    # Normalize tokens (lowercase, remove punctuation)
    normalized = [re.sub(r'[^\w]', '', t.lower()) for t in tokens]
    
    # Check for repetitions within window
    for i in range(len(normalized) - 1):
        word = normalized[i]
        if not word:  # Skip empty strings
            continue
        
        # Check if same word appears within window
        for j in range(i + 1, min(i + window + 1, len(normalized))):
            if normalized[j] == word:
                repetitions.append(word)
                positions.append((word, i, j))
                break  # Count each word only once
    
    return {
        'has_repetition': len(repetitions) > 0,
        'repetition_words': list(set(repetitions)),
        'n_repetitions': len(set(repetitions)),
        'repetition_positions': positions
    }

def detect_discourse_markers_near_switch(tokens: List[str], lang_tags: List[str], 
                                         lang: str, window: int = 2) -> dict:
    """
    Detect if discourse markers appear near code-switch boundaries.
    
    Args:
        tokens: Tokenized words
        lang_tags: Language tags for each token (EN/ZH/HI/CS/OTHER)
        lang: Utterance language
        window: Window size around switch point
    
    Returns dict with:
        - has_discourse_marker_near_switch: bool
        - switch_positions: list of switch positions
        - discourse_marker_at_switch: bool
    """
    if lang != 'CS' or not lang_tags:
        return {
            'has_discourse_marker_near_switch': False,
            'switch_positions': [],
            'discourse_marker_at_switch': False
        }
    
    # Find code-switch positions
    switch_positions = []
    prev_tag = None
    
    for i, tag in enumerate(lang_tags):
        if tag in ['EN', 'ZH', 'HI'] and prev_tag and prev_tag != tag:
            switch_positions.append(i)
        prev_tag = tag
    
    if not switch_positions:
        return {
            'has_discourse_marker_near_switch': False,
            'switch_positions': switch_positions,
            'discourse_marker_at_switch': False
        }
    
    # Check for discourse markers near switches
    marker_info = detect_discourse_markers(tokens, lang)
    marker_words = marker_info.get('discourse_marker_words', [])
    
    if not marker_words:
        return {
            'has_discourse_marker_near_switch': False,
            'switch_positions': switch_positions,
            'discourse_marker_at_switch': False
        }
    
    # Check if markers appear near switch points
    marker_near_switch = False
    for switch_pos in switch_positions:
        for marker in marker_words:
            marker_tokens = marker.lower().split()
            # Check if marker appears within window of switch
            for i in range(max(0, switch_pos - window), 
                          min(len(tokens), switch_pos + window + 1)):
                if i + len(marker_tokens) <= len(tokens):
                    if tokens[i:i+len(marker_tokens)] == marker_tokens:
                        marker_near_switch = True
                        break
    
    return {
        'has_discourse_marker_near_switch': marker_near_switch,
        'switch_positions': switch_positions,
        'discourse_marker_at_switch': marker_near_switch
    }

def process_manifest(manifest_file: str, output_file: str, corpus: str):
    """
    Process manifest file to add discourse marker and repetition annotations.
    """
    print(f"Reading manifest from: {manifest_file}")
    df = pd.read_csv(manifest_file, low_memory=False)
    
    print(f"Total utterances: {len(df)}")
    
    # Initialize new columns
    df['has_discourse_marker'] = False
    df['discourse_marker_type'] = None
    df['n_discourse_markers'] = 0
    df['has_repetition'] = False
    df['n_repetitions'] = 0
    df['has_discourse_marker_near_switch'] = False
    
    # Determine language for discourse marker detection
    lang_map = {
        'EN': 'EN',
        'ZH': 'ZH',
        'HI': 'HI',
        'CS': 'EN' if corpus == 'seame' else 'HI'  # Default to L1
    }
    
    print("\nProcessing utterances...")
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  Processed {idx}/{len(df)} utterances...")
        
        text = row.get('text', '')
        lang = row.get('lang', 'EN')
        
        # Tokenize
        tokens = tokenize_text(text, lang_map.get(lang, 'EN'))
        
        if not tokens:
            continue
        
        # Detect discourse markers
        marker_info = detect_discourse_markers(tokens, lang_map.get(lang, 'EN'))
        df.at[idx, 'has_discourse_marker'] = marker_info['has_discourse_marker']
        df.at[idx, 'discourse_marker_type'] = marker_info.get('discourse_marker_type')
        df.at[idx, 'n_discourse_markers'] = marker_info['n_discourse_markers']
        
        # Detect repetitions
        rep_info = detect_repetitions(tokens)
        df.at[idx, 'has_repetition'] = rep_info['has_repetition']
        df.at[idx, 'n_repetitions'] = rep_info['n_repetitions']
        
        # For CSW utterances, check discourse markers near switches
        if lang == 'CS':
            # Try to get language tags if available
            lang_tags = None
            if 'LID_tags' in row:
                try:
                    import ast
                    lang_tags = ast.literal_eval(str(row['LID_tags']))
                except:
                    pass
            
            if lang_tags:
                switch_info = detect_discourse_markers_near_switch(
                    tokens, lang_tags, lang
                )
                df.at[idx, 'has_discourse_marker_near_switch'] = (
                    switch_info['has_discourse_marker_near_switch']
                )
    
    # Save output
    output_path = pathlib.Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"\nSaved annotated manifest to: {output_file}")
    
    # Print statistics
    print("\n=== Discourse Marker Statistics ===")
    print(f"Utterances with discourse markers: {df['has_discourse_marker'].sum()} "
          f"({100*df['has_discourse_marker'].mean():.1f}%)")
    
    print("\n=== Repetition Statistics ===")
    print(f"Utterances with repetitions: {df['has_repetition'].sum()} "
          f"({100*df['has_repetition'].mean():.1f}%)")
    
    if 'CS' in df['lang'].values:
        cs_df = df[df['lang'] == 'CS']
        print(f"\n=== CSW-Specific Statistics ===")
        print(f"CSW utterances with discourse markers: {cs_df['has_discourse_marker'].sum()} "
              f"({100*cs_df['has_discourse_marker'].mean():.1f}%)")
        print(f"CSW utterances with repetitions: {cs_df['has_repetition'].sum()} "
              f"({100*cs_df['has_repetition'].mean():.1f}%)")
    
    return df

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Detect discourse markers and repetitions in CSW utterances'
    )
    p.add_argument('--manifest', type=str, required=True,
                   help='Input manifest CSV file')
    p.add_argument('--output', type=str, required=True,
                   help='Output manifest CSV with annotations')
    p.add_argument('--corpus', type=str, choices=['seame', 'masac'],
                   default='seame', help='Corpus name')
    
    args = p.parse_args()
    
    manifest_file = pathlib.Path(args.manifest)
    if not manifest_file.exists():
        print(f"ERROR: Manifest file not found: {manifest_file}")
        exit(1)
    
    process_manifest(str(manifest_file), args.output, args.corpus)
