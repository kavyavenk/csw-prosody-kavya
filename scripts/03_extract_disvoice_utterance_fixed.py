#!/usr/bin/env python3
"""
Extract DisVoice prosodic features with scipy compatibility fixes.
"""

# Apply compatibility fixes BEFORE importing disvoice
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.fix_disvoice_compatibility import *

import argparse
import pandas as pd
import pathlib
import tqdm
import time

# Import DisVoice after patches
from disvoice.prosody.prosody import Prosody

p = argparse.ArgumentParser()
p.add_argument("--corpus", choices=["masac","seame"], required=True)
p.add_argument("--limit", type=int, default=None, help="Limit number of files to process (for testing)")
args = p.parse_args()

MAN = pathlib.Path(f"manifests/{args.corpus}_manifest.csv")
CLIPS = pathlib.Path(f"data/{args.corpus}_wav16k_clips")
OUT = pathlib.Path(f"features/{args.corpus}_disvoice_utt.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

if not MAN.exists():
    raise SystemExit(f"Manifest not found: {MAN}")

print("Initializing DisVoice Prosody extractor...")
try:
    pros = Prosody()
    print("✓ DisVoice Prosody initialized")
except Exception as e:
    print(f"✗ Failed to initialize DisVoice: {e}")
    raise

df = pd.read_csv(MAN)
if args.limit:
    df = df.head(args.limit)
    print(f"Processing limited to {args.limit} utterances")

feats = []
print(f"Extracting features from {len(df)} utterances...")

skipped = 0
errors = []

for r in tqdm.tqdm(df.itertuples(), total=len(df)):
    # Get WAV file path from manifest
    wav_file = pathlib.Path(r.wav) if hasattr(r, 'wav') and r.wav else None
    
    # Try the path from manifest first
    audio_path = None
    if wav_file and wav_file.exists():
        audio_path = str(wav_file)
    else:
        # For SEAME: extract filename from manifest path and check both directories
        if args.corpus == "seame":
            # Extract filename from the wav path in manifest
            filename = None
            if wav_file:
                filename = wav_file.name if hasattr(wav_file, 'name') else str(wav_file).split('/')[-1]
            elif hasattr(r, 'wav') and r.wav:
                # Extract from string path
                filename = str(r.wav).split('/')[-1]
            
            # Try multiple locations and filename formats
            seame_dir = pathlib.Path("data/SEAME/interview_aligned/interview_aligned")
            
            # Try 1: clips directory with filename from manifest
            if filename:
                clip_path = CLIPS / filename
                if clip_path.exists():
                    audio_path = str(clip_path)
            
            # Try 2: SEAME directory with filename from manifest
            if not audio_path and filename:
                seame_path = seame_dir / filename
                if seame_path.exists():
                    audio_path = str(seame_path)
            
            # Try 3: clips directory with utt_id.wav (this is what worked for 52K files)
            if not audio_path:
                clip = (CLIPS / f"{r.utt_id}.wav")
                if clip.exists():
                    audio_path = str(clip)
            
            # Try 4: SEAME directory with utt_id.wav
            if not audio_path:
                seame_utt = seame_dir / f"{r.utt_id}.wav"
                if seame_utt.exists():
                    audio_path = str(seame_utt)
        else:
            # For MASAC: try clips directory with utt_id
            clip = (CLIPS / f"{r.utt_id}.wav")
            if clip.exists():
                audio_path = str(clip)
            # For MASAC, also try file_id directly in subdirectories
            elif args.corpus == "masac" and hasattr(r, 'file_id'):
                file_id = r.file_id
                possible_paths = [
                    CLIPS / f"{file_id}.wav",
                    CLIPS / "test" / "audios" / f"{file_id}.wav",
                    CLIPS / "train" / "audios" / f"{file_id}.wav",
                    CLIPS / "val" / "audios" / f"{file_id}.wav",
                ]
                for p in possible_paths:
                    if p.exists():
                        audio_path = str(p)
                        break
    
    if not audio_path:
        skipped += 1
        continue
    
    try:
        # Extract features
        fdict = pros.extract_features_file(audio_path)
        
        # Handle different return types (dict or array)
        if isinstance(fdict, dict):
            feature_dict = fdict
        elif hasattr(fdict, '__len__'):
            # DisVoice prosody returns numpy array, need to get feature names
            feature_dict = {}
            if len(fdict) > 0:
                # Get feature names from prosody object (they're attributes, not methods)
                try:
                    f0_names = pros.namefeatf0 if hasattr(pros, 'namefeatf0') else []
                    dur_names = pros.namefeatdur if hasattr(pros, 'namefeatdur') else []
                    eu_names = pros.namefeatEu if hasattr(pros, 'namefeatEu') else []
                    ev_names = pros.namefeatEv if hasattr(pros, 'namefeatEv') else []
                    
                    # Handle if they're callable or already lists
                    if callable(f0_names):
                        f0_names = f0_names()
                    if callable(dur_names):
                        dur_names = dur_names()
                    if callable(eu_names):
                        eu_names = eu_names()
                    if callable(ev_names):
                        ev_names = ev_names()
                    
                    all_names = list(f0_names) + list(dur_names) + list(eu_names) + list(ev_names)
                    
                    if len(all_names) == len(fdict):
                        feature_dict = {name: float(val) for name, val in zip(all_names, fdict)}
                    else:
                        # Fallback: use generic names
                        feature_dict = {f"feature_{i}": float(v) for i, v in enumerate(fdict)}
                except Exception as name_error:
                    # Fallback: use generic names
                    feature_dict = {f"feature_{i}": float(v) for i, v in enumerate(fdict)}
        else:
            skipped += 1
            errors.append(f"{audio_path}: Unexpected feature format")
            continue
        
        # Verify we got features
        if not feature_dict or len(feature_dict) == 0:
            skipped += 1
            errors.append(f"{audio_path}: No features extracted")
            continue
        
        row = {
            "utt_id": r.utt_id, 
            "speaker": r.speaker, 
            "lang": r.lang, 
            "condition": r.condition
        }
        row.update({k: float(v) if v is not None and not (isinstance(v, float) and (v != v)) else 0.0 
                   for k,v in feature_dict.items()})
        feats.append(row)
        
    except Exception as e:
        skipped += 1
        error_msg = f"{audio_path}: {str(e)}"
        errors.append(error_msg)
        if len(errors) <= 10:
            print(f"\n⚠ skip {error_msg}")

if errors:
    print(f"\nTotal errors: {len(errors)}")
    if len(errors) > 10:
        print(f"  (showing first 10, {len(errors)-10} more...)")

if feats:
    pd.DataFrame(feats).to_csv(OUT, index=False)
    n_features = len(feats[0]) - 4  # Subtract metadata columns
    print(f"\n[{args.corpus}] ✓ Wrote {OUT}")
    print(f"  Successfully extracted: {len(feats)} utterances")
    print(f"  Features per utterance: {n_features} (target: ~103)")
    print(f"  Skipped: {skipped}")
else:
    print(f"\n✗ No features extracted! Check errors above.")
