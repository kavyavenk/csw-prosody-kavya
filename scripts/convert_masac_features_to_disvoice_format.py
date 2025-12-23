#!/usr/bin/env python3
"""
Convert existing MASAC prosodic features to DisVoice-compatible format.

Since DisVoice has scipy compatibility issues, we'll use the existing
prosodic features and adapt them for the statistical analysis.
"""

import argparse
import pandas as pd
import pathlib

def convert_features(input_csv, output_csv):
    """Convert MASAC prosodic features to analysis format."""
    
    print(f"Reading existing features from: {input_csv}")
    df = pd.read_csv(input_csv, low_memory=False)
    
    print(f"Total utterances: {len(df)}")
    
    # Map language labels
    lang_map = {
        'CSW': 'CS',
        'EN': 'EN',
        'HI': 'HI'
    }
    df['lang'] = df['Language from LID tool'].map(lang_map).fillna('UNK')
    
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
    
    # Filter out unknown
    df = df[df['lang'] != 'UNK']
    
    # Extract prosodic features
    prosodic_cols = [
        'Minimum pitch', 'Mean pitch', 'Maximum pitch', 'Std Dev Pitch',
        'Minimum intensity', 'Mean intensity', 'Maximum intensity', 'Std Dev Intensity',
        'Jitter', 'Shimmer', 'HNR', 'Speaking rate'
    ]
    
    # Create output DataFrame
    output_rows = []
    
    for _, row in df.iterrows():
        file_name = row['name']  # e.g., "test_10_0.wav"
        file_id = file_name.replace('.wav', '')
        
        # Create utterance ID
        utt_id = file_id
        
        # Build row with prosodic features
        output_row = {
            'utt_id': utt_id,
            'file_id': file_id,
            'speaker': row.get('Speaker', 'unknown'),
            'lang': row['lang'],
            'condition': row['condition'],
        }
        
        # Add prosodic features
        for col in prosodic_cols:
            if col in row:
                output_row[col.lower().replace(' ', '_')] = row[col]
        
        output_rows.append(output_row)
    
    output_df = pd.DataFrame(output_rows)
    
    # Save
    output_path = pathlib.Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    print(f"\nWrote converted features to: {output_csv}")
    print(f"  - Total utterances: {len(output_df)}")
    print(f"\nLanguage distribution:")
    lang_counts = output_df['lang'].value_counts()
    for lang, count in lang_counts.items():
        pct = 100 * count / len(output_df)
        print(f"  {lang}: {count} ({pct:.1f}%)")
    
    print(f"\nProsodic features included: {len(prosodic_cols)}")
    print(f"  {', '.join(prosodic_cols)}")
    
    return output_df

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Convert MASAC prosodic features to analysis format')
    p.add_argument('--input', type=str,
                   default='data/masac_raw/with acoustic-prosodic features.csv',
                   help='Input CSV with prosodic features')
    p.add_argument('--output', type=str,
                   default='features/masac_prosodic_features.csv',
                   help='Output CSV in analysis format')
    
    args = p.parse_args()
    
    convert_features(args.input, args.output)

