# MASAC Prosody Analysis Setup

## Overview

This document describes the setup for replicating the Spanish-English code-switching prosody findings on the MASAC (Hindi-English) corpus.

## What Has Been Completed

### 1. Manifest Building ✅
- Created script: `scripts/01_build_manifest_masac_from_words.py`
- Aggregates word-level language annotations to utterance-level labels
- Handles CSW, monolingual Hindi, and monolingual English utterances
- Manifest created: `manifests/masac_manifest.csv`

### 2. Pipeline Scripts ✅
- **`scripts/12_run_masac_prosody_analysis.py`**: Full pipeline runner
- **`scripts/13_generate_masac_prosody_report.py`**: Report generator comparing to Spanish-English findings
- Updated `scripts/02_slice_by_timestamps.py` to handle MASAC files (already utterances)
- Updated `scripts/03_extract_disvoice_utterance.py` to work with MASAC structure
- Updated `scripts/04_first_contrasts.py` to generate separate CS vs HI and CS vs EN comparisons

### 3. Current Status
- ✅ Manifest built from `masac_words_sample.csv` (5 utterances)
- ⏳ Waiting for audio files to extract features
- ⏳ Statistical analysis pending (requires features)

## To Complete the Analysis

### Step 1: Prepare Audio Files
MASAC audio files need to be placed in one of these locations:
- `data/masac_wav16k/` (16kHz mono WAV files)
- `data/masac_wav16k_clips/` (if already sliced)

**Note**: For MASAC, each file is already an utterance, so files should be named like:
- `train_337_0.wav`
- `train_91_2.wav`
- etc.

### Step 2: Run Full Pipeline

```bash
# Run the complete analysis pipeline
python scripts/12_run_masac_prosody_analysis.py --words data/masac_raw/masac_words_sample.csv
```

This will:
1. Build manifest (if not already done)
2. Slice audio files (if needed)
3. Extract DisVoice prosodic features (103 features)
4. Run statistical comparisons (t-tests with FDR correction)
5. Generate summary report

### Step 3: View Results

Results will be in:
- `features/first_contrast_masac_CS_vs_EN.csv` - CSW vs monolingual English
- `features/first_contrast_masac_CS_vs_HI.csv` - CSW vs monolingual Hindi
- `reports/masac_prosody_analysis.md` - Summary report

## Using Full Dataset

To use the full MASAC dataset instead of the sample:

1. Export word-level annotations:
```bash
python scripts/09_export_words_for_annotation.py \
    --input data/masac_raw/masac_data_compiled.csv \
    --output data/masac_raw/masac_words_full.csv
```

2. Manually update language tags in the CSV (if needed)

3. Run analysis on full dataset:
```bash
python scripts/12_run_masac_prosody_analysis.py \
    --words data/masac_raw/masac_words_full.csv
```

## Expected Findings (Based on Spanish-English Paper)

The Spanish-English paper found:
- **Duration features**: ~96% differ significantly from monolingual
- **Energy features**: ~87.5% differ significantly  
- **Pitch features**: Up to 30% similar (least affected)

**Pattern**: Duration > Energy > Pitch

We expect to test if this pattern generalizes to Hindi-English code-switching.

## Methodology Alignment

✅ **Feature Extraction**: DisVoice 103 prosodic features
✅ **Statistical Test**: Independent t-tests (Welch's for unequal variances)
✅ **Multiple Comparisons**: Benjamini-Hochberg FDR correction (α=0.05)
✅ **Effect Size**: Cohen's d
✅ **Comparisons**: CSW vs. monolingual Hindi, CSW vs. monolingual English

## Files Created

- `manifests/masac_manifest.csv` - Utterance manifest
- `scripts/01_build_manifest_masac_from_words.py` - Manifest builder
- `scripts/12_run_masac_prosody_analysis.py` - Pipeline runner
- `scripts/13_generate_masac_prosody_report.py` - Report generator

## Next Steps

1. **Add audio files** to `data/masac_wav16k/` or `data/masac_wav16k_clips/`
2. **Run the pipeline**: `python scripts/12_run_masac_prosody_analysis.py`
3. **Review results** in `features/` and `reports/`
4. **Compare findings** to Spanish-English patterns

## Troubleshooting

### "No audio files found"
- Ensure WAV files are in `data/masac_wav16k/` or `data/masac_wav16k_clips/`
- Check file naming matches the manifest (e.g., `train_337_0.wav`)

### "DisVoice not found"
- Install: `pip install disvoice`

### "Feature extraction failed"
- Check audio file format (should be 16kHz mono WAV)
- Verify audio files are readable
- Check file paths in manifest

### "Statistical analysis failed"
- Ensure features have been extracted first
- Check that you have utterances in all conditions (CSW, EN, HI)
- Minimum 5 utterances per condition recommended

