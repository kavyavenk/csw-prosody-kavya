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
    cmd = [
        "ffmpeg","-y","-i", r.wav,
        "-ss", str(r.start), "-to", str(r.end),
        "-ac","1","-ar","16000",
        str(out)
    ]
    subprocess.run(cmd, check=True)
    n += 1
print(f"[{args.corpus}] Sliced {n} utterance clips into {CLIPS_DIR}")
