# How to Obtain MASAC Audio Files

## Current Status

Based on my search, **MASAC audio files are NOT publicly available online**. The corpus appears to be restricted and requires contacting the corpus maintainers for access.

**What I Found:**
- ✅ You have transcripts and annotations (6,476 utterances)
- ✅ File names are referenced (e.g., `train_337_0.wav`, `test_100_0.wav`)
- ❌ Audio files are NOT in the zip file (`MaSaC-20251015T043423Z-1-001.zip`)
- ❌ No public download links found online
- ❌ No GitHub repository with audio files found

## What I Found

1. **No Public Downloads**: Web searches did not find any publicly available MASAC audio files
2. **Zip File in Repository**: There's a zip file `data/MaSaC-20251015T043423Z-1-001.zip` in your data directory - this may contain audio files
3. **Transcripts Available**: You have transcripts and annotations in `data/masac_raw/`

## Steps to Obtain Audio Files

### Option 1: Check the Existing Zip File

The zip file `data/MaSaC-20251015T043423Z-1-001.zip` might contain audio files:

```bash
# Extract and check contents
cd data
unzip -l MaSaC-20251015T043423Z-1-001.zip | grep -i "\.wav"
unzip MaSaC-20251015T043423Z-1-001.zip
```

If it contains audio files, you can organize them:
```bash
# Move WAV files to the expected location
mkdir -p masac_wav16k
find . -name "*.wav" -exec mv {} masac_wav16k/ \;
```

### Option 2: Contact MASAC Corpus Maintainers

Since MASAC is not publicly available, you'll need to:

1. **Find the Original Paper/Repository**:
   - Search for papers mentioning "MASAC" or "MaSaC" corpus
   - Look for authors from IIT Bombay or other Indian institutions
   - Check if there's a GitHub repository or project page

2. **Contact Information**:
   - Email the authors of papers using MASAC
   - Contact the institution (likely IIT Bombay based on naming conventions)
   - Check if there's a data request form or agreement

3. **Request Access**:
   - Explain your research purpose (prosody analysis)
   - Agree to any usage terms or licensing agreements
   - Provide institutional affiliation if required

### Option 3: Check Academic Repositories

Try these resources:
- **Linguistic Data Consortium (LDC)**: https://www.ldc.upenn.edu/
- **OpenSLR**: http://www.openslr.org/
- **Hugging Face Datasets**: https://huggingface.co/datasets
- **Papers with Code**: https://paperswithcode.com/

### Option 4: Alternative Approach

If audio files are unavailable, you could:

1. **Use Synthetic Audio**: Generate TTS audio from transcripts (not ideal for prosody research)
2. **Focus on Transcript Analysis**: Analyze linguistic patterns without audio
3. **Use Alternative Corpus**: Consider other Hindi-English code-switching corpora

## Expected File Structure

Once you have audio files, they should be organized as:

```
data/masac_wav16k/
  ├── train_337_0.wav
  ├── train_91_2.wav
  ├── train_213_4.wav
  ├── train_249_3.wav
  ├── train_193_0.wav
  └── ... (one file per utterance)
```

Each file corresponds to one utterance in your `masac_data_compiled.csv`.

## Verification

After obtaining audio files, verify they match your transcripts:

```bash
# Check if audio files exist for your sample
python scripts/check_audio_availability.py
```

Or manually:
```bash
cd data/masac_wav16k
ls train_337_0.wav train_91_2.wav train_213_4.wav train_249_3.wav train_193_0.wav
```

## Next Steps

1. **Check the zip file first** - it might already contain what you need
2. **If not, search for MASAC papers** to find contact information
3. **Request access** from corpus maintainers
4. **Once you have audio files**, run:
   ```bash
   python scripts/12_run_masac_prosody_analysis.py
   ```

## Resources to Check

- **Google Scholar**: Search "MASAC corpus Hindi English code-switching"
- **ACL Anthology**: Check papers mentioning MASAC
- **GitHub**: Search for "MASAC" or "MaSaC" repositories
- **ResearchGate**: Look for authors who used MASAC

## Note

The MASAC corpus appears to be a research dataset that may require:
- Academic affiliation
- Research purpose statement
- Data usage agreement
- Possibly a fee or institutional access

Be prepared to provide these when requesting access.

