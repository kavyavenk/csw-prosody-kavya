# Pilot Testing Setup Summary

## What We've Created

### 1. Methodology Documentation (`METHODOLOGY.md`)
Comprehensive explanation of the Spanish-English prosody paper:
- Research questions and corpus details
- Feature extraction (DisVoice 103 features)
- Statistical methods (t-tests, FDR correction, Cohen's d)
- Key findings (duration > energy > pitch pattern)
- Replication strategy for SEAME and MASAC

### 2. Pilot Subset Selection Script (`scripts/07_pilot_subset_selection.py`)
Selects balanced subsets for initial testing:
- Configurable number of utterances per condition (default: 100)
- Duration filtering (0.5s - 10s default)
- Speaker balance across conditions
- Audio file availability checking

**Usage:**
```bash
python scripts/07_pilot_subset_selection.py --corpus seame --n_per_condition 100
python scripts/07_pilot_subset_selection.py --corpus masac --n_per_condition 100
```

### 3. Corpus Comparison Report Generator (`scripts/08_corpus_comparison_report.py`)
Generates comparison reports between SEAME and MASAC:
- Data availability statistics
- Language distribution
- Speaker information
- Code-switching percentages
- Methodology alignment checks

**Usage:**
```bash
python scripts/08_corpus_comparison_report.py
```

### 4. Enhanced Exploration Script (`scripts/00_explore_corpus_data.py`)
Updated to handle SEAME data location correctly.

## Key Findings from Spanish-English Paper

### Methods:
1. **DisVoice 103 prosodic features**: F0, energy, duration features
2. **Statistical testing**: Independent t-tests with Benjamini-Hochberg FDR correction
3. **Effect sizes**: Cohen's d for quantifying differences
4. **Comparisons**: CSW vs. monolingual_EN, CSW vs. monolingual_ZH/HI

### Results:
1. **Duration features**: ~96% differ significantly from monolingual
2. **Energy features**: ~87.5% differ significantly
3. **Pitch features**: Up to 30% similar to monolingual (least affected)
4. **Overall**: CSW prosody more similar to monolingual Spanish than English

## Next Steps for Pilot Testing

### 1. Fix Data Reading Issues
The SEAME CSV may have encoding or format issues. Check:
- Column names and data types
- Missing values handling
- Time format (milliseconds vs seconds)

### 2. Run Exploration Scripts
```bash
# First, check data format
python scripts/00_explore_corpus_data.py --corpus seame > seame_exploration.log 2>&1
python scripts/00_explore_corpus_data.py --corpus masac > masac_exploration.log 2>&1
```

### 3. Build Manifests
Update manifest building scripts to handle:
- SEAME: Timestamps in milliseconds, language labels (CS/EN/ZH)
- MASAC: Individual utterance files, language labels (CSW/EN/HI)

**Current scripts:**
- `scripts/01_build_manifest.py` - Generic manifest builder
- `scripts/01_build_manifest_masac.py` - MASAC-specific (needs completion)

### 4. Select Pilot Subsets
```bash
python scripts/07_pilot_subset_selection.py --corpus seame --n_per_condition 100
python scripts/07_pilot_subset_selection.py --corpus masac --n_per_condition 100
```

### 5. Extract Audio Clips
```bash
python scripts/02_slice_by_timestamps.py --corpus seame
python scripts/02_slice_by_timestamps.py --corpus masac
```

### 6. Extract DisVoice Features
```bash
python scripts/03_extract_disvoice_utterance.py --corpus seame
python scripts/03_extract_disvoice_utterance.py --corpus masac
```

### 7. Run Statistical Comparisons
```bash
python scripts/04_first_contrasts.py --corpus seame
python scripts/04_first_contrasts.py --corpus masac
```

## Data Structure Notes

### SEAME:
- CSV location: `data/SEAME/SEAME_data_annotation_new_2015_annotated_4_17_24.csv`
- Timestamps: `start_time`, `end_time` (in milliseconds)
- Language labels: `language` column (CS, EN, ZH)
- Speakers: `speaker` column
- Code-switching info: `number_of_code_switches` column

### MASAC:
- CSV location: `data/masac_raw/masac_data_compiled.csv`
- Language labels: `Language` column (CSW, EN, HI)
- LID tags: `LID_tags` column (list format)
- Audio files: Individual `.wav` files per utterance
- Timestamps: May need to be extracted from audio files or JSON files

## Expected Outcomes

### For Pilot Testing:
- Balanced subsets: 100-200 utterances per condition
- Feature extraction: 103 DisVoice features per utterance
- Initial contrasts: CS vs. monolingual_EN and CS vs. monolingual_ZH/HI
- Effect sizes: Cohen's d values for significant features

### For Full Replication:
- Validate duration > energy > pitch pattern
- Compare cross-linguistic effects (tonal vs. non-tonal)
- Examine speaker proficiency effects (if metadata available)
- Mixed-effects modeling for speaker-level variation

## Troubleshooting

### If data reading fails:
1. Check CSV encoding (try `encoding='utf-8'` or `encoding='latin-1'`)
2. Check for problematic columns with mixed types
3. Use `low_memory=False` or `dtype` specifications
4. Inspect first few rows manually

### If manifest building fails:
1. Verify column names match expected format
2. Check timestamp format (ms vs seconds)
3. Verify audio file paths exist
4. Check language label mapping

### If audio slicing fails:
1. Verify ffmpeg is installed
2. Check audio file paths in manifest
3. Verify timestamps are valid (start < end)
4. Check audio file format compatibility

## Questions to Address

1. **Speaker metadata**: Do we have proficiency information for SEAME/MASAC?
2. **Audio alignment**: Are timestamps accurate for SEAME? How to handle MASAC?
3. **CSW annotation**: Are CSW boundaries clearly marked?
4. **Balanced sampling**: How to ensure speaker balance across conditions?

## References

- Methodology document: `METHODOLOGY.md`
- DisVoice documentation: https://disvoice.readthedocs.io/en/latest/Prosody.html
- Original paper: Spanish-English CSW Prosody PDF in repository

