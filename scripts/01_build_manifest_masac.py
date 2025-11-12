import pathlib, pandas as pd

RAW = pathlib.Path("data/masac_raw")
WAV = pathlib.Path("data/masac_wav16k")
MAN = pathlib.Path("manifests/masac_manifest.csv")
MAN.parent.mkdir(parents=True, exist_ok=True)

rows = []
# NOTE: EDIT this section to match MaSaC transcript schema.
# The code expects per-utterance rows with columns:
#   file_id, start_sec, end_sec, spk, lang (EN/HI/CS), text
#
# Example loader for TSVs (update glob and column names as needed):
tsvs = list(RAW.rglob("*.tsv"))
if not tsvs:
    print("No .tsv transcripts found under", RAW.resolve(),
          "\nPlease edit scripts/01_build_manifest_masac.py to your transcript format.")
else:
    for tfile in tsvs:
        df = pd.read_csv(tfile, sep="\t")
        # --- EDIT column mappings here ---
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
        required = ["file_id","start_sec","end_sec","spk","lang"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}' in {tfile}. Please edit parser.")
        if "text" not in df.columns:
            df["text"] = ""
        for r in df.itertuples(index=False):
            wav_path = (WAV / f"{r.file_id}.wav").as_posix()
            lang = getattr(r, "lang")
            cond = "code_switched" if lang == "CS" else ("monolingual_EN" if lang=="EN" else "monolingual_HI")
            rows.append({
                "utt_id": f"{r.file_id}_{float(r.start_sec):.3f}_{float(r.end_sec):.3f}",
                "file_id": r.file_id,
                "wav": wav_path,
                "start": float(r.start_sec),
                "end": float(r.end_sec),
                "speaker": getattr(r, "spk"),
                "lang": lang,
                "condition": cond,
                "text": str(getattr(r, "text","")),
            })

    out = pd.DataFrame(rows)
    if not out.empty:
        out.to_csv(MAN, index=False)
        print(f"Wrote {MAN} with {len(out)} utterances")
    else:
        print("No rows produced; please verify transcript parsing.")
