# Current Pipeline Status

## ✅ Completed

1. **SEAME Manifest**: Built with 110,145 utterances
   - CSW: 56,739 (51.5%)
   - EN: 28,655 (26.0%)
   - ZH: 24,751 (22.5%)

2. **SEAME Audio Clips**: 33,197 clips ready in `data/seame_wav16k_clips/`

3. **MASAC Manifest**: Built with 5 utterances (sample)
   - Need to rebuild with full dataset

4. **MASAC Audio Files**: 9,078 files found in `data/masac_wav16k_clips/`

5. **DisVoice**: Installed and ready

## 🔄 In Progress

1. **SEAME Feature Extraction**: Running in background
   - Extracting DisVoice 103 prosodic features from 33K clips
   - This will take some time

## ⏳ Pending

1. **MASAC Manifest Update**: Need to rebuild manifest to match actual audio file locations
2. **MASAC Feature Extraction**: After manifest is updated
3. **Statistical Analysis**: For both SEAME and MASAC
   - CSW vs monolingual comparisons
   - FDR correction
   - Cohen's d effect sizes
4. **Report Generation**: Compare findings to Spanish-English paper

## Next Steps

1. **Wait for SEAME features** to finish extracting (running in background)
2. **Update MASAC manifest** to point to correct audio file paths
3. **Extract MASAC features** once manifest is updated
4. **Run statistical comparisons** for both corpora
5. **Generate comparison reports**

## Quick Commands

```bash
# Check SEAME feature extraction progress
tail -f features/seame_disvoice_utt.csv  # (when it starts writing)

# Update MASAC manifest (once we fix paths)
python scripts/01_build_manifest_masac_from_words.py --words data/masac_raw/masac_words_sample.csv

# Run statistical analysis (once features are extracted)
python scripts/04_first_contrasts.py --corpus seame
python scripts/04_first_contrasts.py --corpus masac

# Generate reports
python scripts/13_generate_masac_prosody_report.py
```

