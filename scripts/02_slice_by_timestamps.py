import argparse, subprocess, pandas as pd, pathlib

p = argparse.ArgumentParser()
p.add_argument("--corpus", choices=["masac","seame"], required=True)
args = p.parse_args()

MAN = pathlib.Path(f"manifests/{args.corpus}_manifest.csv")
CLIPS_DIR = pathlib.Path(f"data/{args.corpus}_wav16k_clips")
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

if not MAN.exists():
    raise SystemExit(f"Manifest not found: {MAN}")

df = pd.read_csv(MAN)
n = 0
for r in df.itertuples():
    out = CLIPS_DIR / f"{r.utt_id}.wav"
    if out.exists():
        continue
    
    wav_path = pathlib.Path(r.wav)
    
    # For MASAC, if start=0 and end=-1 or end=duration, the file is already an utterance
    # Just copy/convert it instead of slicing
    if args.corpus == "masac" and r.start == 0.0 and (r.end < 0 or not wav_path.exists()):
        # If original file exists, copy and convert it
        # Try to find the original file
        file_id = getattr(r, 'file_id', None)
        if file_id:
            # Try common locations
            possible_paths = [
                pathlib.Path(f"data/masac_wav16k/{file_id}.wav"),
                pathlib.Path(f"data/masac_raw/{file_id}.wav"),
                wav_path
            ]
            for src in possible_paths:
                if src.exists():
                    cmd = ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", "16000", str(out)]
                    subprocess.run(cmd, check=True)
                    n += 1
                    break
        continue
    
    # For SEAME, files are already sliced, so just copy/convert
    if args.corpus == "seame":
        if wav_path.exists():
            # File already exists and is sliced, just convert to 16kHz mono
            cmd = ["ffmpeg", "-y", "-i", str(wav_path), "-ac", "1", "-ar", "16000", str(out)]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                n += 1
            except subprocess.CalledProcessError:
                pass  # Skip if conversion fails
        continue
    
    # Normal slicing for MASAC with timestamps
    if not wav_path.exists():
        continue
    
    if r.end < 0:
        # If end is negative, use the whole file
        cmd = ["ffmpeg", "-y", "-i", str(wav_path), "-ac", "1", "-ar", "16000", str(out)]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", str(wav_path),
            "-ss", str(r.start), "-to", str(r.end),
            "-ac", "1", "-ar", "16000",
            str(out)
        ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        n += 1
    except subprocess.CalledProcessError:
        pass  # Skip if slicing fails
print(f"[{args.corpus}] Sliced {n} utterance clips into {CLIPS_DIR}")
