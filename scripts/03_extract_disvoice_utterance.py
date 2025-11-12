import argparse, pandas as pd, pathlib, tqdm
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

pros = Prosody()

df = pd.read_csv(MAN)
feats = []
for r in tqdm.tqdm(df.itertuples(), total=len(df)):
    clip = (CLIPS / f"{r.utt_id}.wav")
    if not clip.exists():
        continue
    try:
        fdict = pros.extract_features_file(str(clip))
        row = {"utt_id": r.utt_id, "speaker": r.speaker, "lang": r.lang, "condition": r.condition}
        row.update({k: float(v) for k,v in fdict.items()})
        feats.append(row)
    except Exception as e:
        print("skip", clip, e)

pd.DataFrame(feats).to_csv(OUT, index=False)
print(f"[{args.corpus}] Wrote {OUT} with {len(feats)} rows")
