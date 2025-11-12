import argparse, subprocess, pathlib, sys
p = argparse.ArgumentParser()
p.add_argument("--corpus", choices=["masac","seame"], required=True)
args = p.parse_args()

SRC = pathlib.Path(f"data/{args.corpus}_raw")
DST = pathlib.Path(f"data/{args.corpus}_wav16k")
DST.mkdir(parents=True, exist_ok=True)

wavs = list(SRC.rglob("*.wav"))
if not wavs:
    print("No WAV files found under", SRC.resolve())
    sys.exit(0)

for wav in wavs:
    out = DST / wav.relative_to(SRC)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg","-y","-i",str(wav),"-ac","1","-ar","16000","-sample_fmt","s16",str(out)]
    subprocess.run(cmd, check=True)
print(f"[{args.corpus}] Normalized {len(wavs)} files →", DST)
