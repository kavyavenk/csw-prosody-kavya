#!/usr/bin/env python3
"""
Check which MASAC audio files are available.

This script checks which audio files referenced in the manifest
actually exist in the filesystem.
"""

import argparse
import pathlib
import pandas as pd

def check_audio_availability(manifest_file, wav_dirs):
    """Check which audio files are available."""
    
    if not pathlib.Path(manifest_file).exists():
        print(f"ERROR: Manifest not found: {manifest_file}")
        return
    
    print(f"Reading manifest: {manifest_file}")
    df = pd.read_csv(manifest_file)
    
    print(f"\nTotal utterances in manifest: {len(df)}")
    
    # Check multiple possible locations
    found_files = []
    missing_files = []
    
    for _, row in df.iterrows():
        file_id = row['file_id']
        wav_name = f"{file_id}.wav"
        
        found = False
        location = None
        
        # Check in various locations
        for wav_dir in wav_dirs:
            wav_path = pathlib.Path(wav_dir) / wav_name
            if wav_path.exists():
                found = True
                location = str(wav_path)
                break
        
        if found:
            found_files.append((file_id, location))
        else:
            missing_files.append(file_id)
    
    # Report results
    print(f"\n{'='*60}")
    print(f"Audio File Availability Check")
    print(f"{'='*60}")
    print(f"Found: {len(found_files)} / {len(df)} ({100*len(found_files)/len(df):.1f}%)")
    print(f"Missing: {len(missing_files)} / {len(df)} ({100*len(missing_files)/len(df):.1f}%)")
    
    if found_files:
        print(f"\n✅ Found files (first 10):")
        for file_id, location in found_files[:10]:
            print(f"  - {file_id}.wav")
    
    if missing_files:
        print(f"\n❌ Missing files (first 10):")
        for file_id in missing_files[:10]:
            print(f"  - {file_id}.wav")
    
    # Check by condition
    if 'condition' in df.columns:
        print(f"\n{'='*60}")
        print(f"Availability by Condition")
        print(f"{'='*60}")
        for condition in df['condition'].unique():
            cond_df = df[df['condition'] == condition]
            cond_found = sum(1 for f in cond_df['file_id'] 
                           if any((pathlib.Path(d) / f"{f}.wav").exists() for d in wav_dirs))
            print(f"{condition}: {cond_found}/{len(cond_df)} ({100*cond_found/len(cond_df):.1f}%)")
    
    return {
        'found': len(found_files),
        'missing': len(missing_files),
        'total': len(df),
        'found_files': found_files,
        'missing_files': missing_files
    }

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Check MASAC audio file availability')
    p.add_argument('--manifest', type=str,
                   default='manifests/masac_manifest.csv',
                   help='Manifest file path')
    p.add_argument('--wav-dirs', type=str, nargs='+',
                   default=['data/masac_wav16k', 'data/masac_wav16k_clips', 'data/masac_raw'],
                   help='Directories to check for WAV files')
    
    args = p.parse_args()
    
    check_audio_availability(args.manifest, args.wav_dirs)

