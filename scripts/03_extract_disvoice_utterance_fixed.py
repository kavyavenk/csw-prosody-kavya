#!/usr/bin/env python3
"""
Extract DisVoice prosodic features with scipy compatibility fixes.
"""

# Apply compatibility fixes BEFORE importing disvoice
import sys
sys.path.insert(0, 'scripts')
from fix_disvoice_compatibility import *

import argparse
import pandas as pd
import pathlib
import tqdm
from disvoice.prosody.prosody import Prosody

p = argparse.ArgumentParser()
p.add_argument("--corpus", choices=["masac","seame"], required=True)
args = p.parse_args()

MAN = pathlib.Path(f"manifests/{args.corpus}_manifest.csv")
CLIPS = pathlib.Path(f"data/{args.corpus}_wav16k_clips")
OUT = pathlib.Path(f"features/{args.corpus}_disvoice_utt.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

if not MAN.exists():
    raise SystemExit(f"Manifest not found: {MAN}")

print("Initializing DisVoice Prosody extractor...")
pros = Prosody()

df = pd.read_csv(MAN)
feats = []
print(f"Extracting features from {len(df)} utterances...")

skipped = 0
for r in tqdm.tqdm(df.itertuples(), total=len(df)):
    # Get WAV file path from manifest
    wav_file = pathlib.Path(r.wav) if hasattr(r, 'wav') and r.wav else None
    
    # Try the path from manifest first
    audio_path = None
    if wav_file and wav_file.exists():
        audio_path = str(wav_file)
    else:
        # Fallback: try clips directory with utt_id
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
        fdict = pros.extract_features_file(audio_path)
        row = {"utt_id": r.utt_id, "speaker": r.speaker, "lang": r.lang, "condition": r.condition}
        row.update({k: float(v) for k,v in fdict.items()})
        feats.append(row)
    except Exception as e:
        skipped += 1
        if skipped <= 10:  # Only print first 10 errors
            print(f"\nskip {audio_path}: {e}")

if skipped > 10:
    print(f"\n... and {skipped - 10} more files skipped")

pd.DataFrame(feats).to_csv(OUT, index=False)
print(f"\n[{args.corpus}] Wrote {OUT} with {len(feats)} rows")
print(f"  Successfully extracted: {len(feats)}")
print(f"  Skipped: {skipped}")
print(f"  Features per utterance: {len(feats[0]) - 4 if feats else 0} (should be ~103)")
