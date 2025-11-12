import argparse, pathlib, pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--corpus", choices=["masac","seame"], required=True)
args = p.parse_args()

RAW = pathlib.Path(f"data/{args.corpus}_raw")
WAV = pathlib.Path(f"data/{args.corpus}_wav16k")
MAN = pathlib.Path(f"manifests/{args.corpus}_manifest.csv")
MAN.parent.mkdir(parents=True, exist_ok=True)

rows = []

if args.corpus == "masac":
    # TODO: EDIT to match MaSaC transcript files/columns
    # Expect columns: file_id, start_sec, end_sec, spk, lang (EN/HI/CS), text
    tsvs = list(RAW.rglob("*.tsv"))
    if not tsvs:
        print("No .tsv transcripts found under", RAW.resolve())
    for t in tsvs:
        df = pd.read_csv(t, sep="\t")
        # ---- EDIT column mappings here ----
        mapping = {
            # "audio_id":"file_id",
            # "start_time":"start_sec",
            # "end_time":"end_sec",
            # "speaker":"spk",
            # "lang_label":"lang",
            # "transcript":"text",
        }
        for k,v in mapping.items():
            if k in df.columns: df = df.rename(columns={k:v})
        req = ["file_id","start_sec","end_sec","spk","lang"]
        for col in req:
            if col not in df.columns:
                raise ValueError(f"[masac] Missing column {col} in {t}")
        if "text" not in df.columns: df["text"]=""
        for r in df.itertuples(index=False):
            lang = getattr(r,"lang")
            cond = "code_switched" if lang=="CS" else ("monolingual_EN" if lang=="EN" else "monolingual_HI")
            rows.append({
                "utt_id": f"{r.file_id}_{float(r.start_sec):.3f}_{float(r.end_sec):.3f}",
                "file_id": r.file_id,
                "wav": (WAV / f"{r.file_id}.wav").as_posix(),
                "start": float(r.start_sec),
                "end": float(r.end_sec),
                "speaker": getattr(r,"spk"),
                "lang": lang,
                "condition": cond,
                "text": str(getattr(r,"text",""))
            })

elif args.corpus == "seame":
    # TODO: EDIT to match SEAME transcripts (phase I/II)
    # Expect columns: file_id, start_sec, end_sec, spk, lang (EN/ZH/CS), text
    exts = ["*.tsv","*.csv"]
    files = []
    for e in exts: files += list(RAW.rglob(e))
    if not files:
        print("No transcripts found under", RAW.resolve())
    for t in files:
        if t.suffix == ".tsv":
            df = pd.read_csv(t, sep="\t")
        else:
            df = pd.read_csv(t)
        mapping = {
            # "audio_id":"file_id",
            # "StartTime":"start_sec",
            # "EndTime":"end_sec",
            # "Speaker":"spk",
            # "Lang":"lang",
            # "Utterance":"text",
        }
        for k,v in mapping.items():
            if k in df.columns: df = df.rename(columns={k:v})
        req = ["file_id","start_sec","end_sec","spk","lang"]
        for col in req:
            if col not in df.columns:
                raise ValueError(f"[seame] Missing column {col} in {t}")
        if "text" not in df.columns: df["text"]=""
        for r in df.itertuples(index=False):
            lang = getattr(r,"lang")
            cond = "code_switched" if lang=="CS" else ("monolingual_EN" if lang=="EN" else "monolingual_ZH")
            rows.append({
                "utt_id": f"{r.file_id}_{float(r.start_sec):.3f}_{float(r.end_sec):.3f}",
                "file_id": r.file_id,
                "wav": (WAV / f"{r.file_id}.wav").as_posix(),
                "start": float(r.start_sec),
                "end": float(r.end_sec),
                "speaker": getattr(r,"spk"),
                "lang": lang,
                "condition": cond,
                "text": str(getattr(r,"text",""))
            })

out = pd.DataFrame(rows)
if not out.empty:
    out.to_csv(MAN, index=False)
    print(f"[{args.corpus}] Wrote {MAN} with {len(out)} utterances")
else:
    print(f"[{args.corpus}] No rows produced; please verify transcript parsing.")
