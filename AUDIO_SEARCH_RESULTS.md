# MASAC Audio Files Search Results

## Search Summary

**Date**: Current search
**Location Checked**: `data/masac_raw/` and entire `data/` directory

## Results

### ❌ No WAV Files Found
- **0 WAV files** found in `data/masac_raw/`
- **0 WAV files** found anywhere in the repository with "masac" in the path
- Only SEAME audio files found (in `data/SEAME/interview_aligned/`)

### ✅ What We Found Instead

1. **File References in CSVs**:
   - `masac_data_compiled.csv` references 6,476 WAV files (e.g., `train_337_0.wav`, `test_100_0.wav`)
   - `with acoustic-prosodic features.csv` references 1,622 WAV files
   - File naming pattern: `{split}_{number}_{utterance_idx}.wav`
     - Examples: `train_337_0.wav`, `test_100_0.wav`, `val_50_1.wav`

2. **Prosodic Features Already Extracted**:
   - `with acoustic-prosodic features.csv` contains prosodic features for 1,622 utterances
   - This proves audio files **DO exist somewhere** (features were extracted from them)

3. **JSON Files with Timestamps**:
   - `train_data_final_plain.json`, `test_data_final_plain.json`, `val_data_final_plain.json`
   - Contain `start_time` and `end_time` fields, suggesting audio file references

## Where Audio Files Might Be

### Possibility 1: Separate Download/Location
Audio files are likely stored separately due to size:
- May be in a different directory not included in this repository
- May require separate download from corpus maintainers
- May be on a shared drive or external storage

### Possibility 2: Need to Extract from Source
Audio files might need to be:
- Extracted from original MASAC corpus download
- Requested from corpus maintainers
- Downloaded from a separate repository/archive

### Possibility 3: Already Processed
Audio files may have been:
- Processed and then deleted to save space
- Stored in a different location (check parent directories)
- Archived in a zip file we haven't checked yet

## Next Steps to Find Audio Files

1. **Check Parent Directories**:
   ```bash
   find .. -name "*.wav" -type f | grep -i masac
   ```

2. **Check for Zip Files**:
   ```bash
   find . -name "*.zip" -exec unzip -l {} \; | grep -i "\.wav"
   ```

3. **Check JSON for Audio Paths**:
   ```bash
   grep -r "audio\|wav\|path" data/masac_raw/*.json
   ```

4. **Contact Source**:
   - Check if there's a README or documentation about audio file location
   - Contact whoever provided the MASAC data
   - Check the original MASAC corpus repository/website

## Current Status

✅ **We have**:
- Transcripts and annotations (6,476 utterances)
- Prosodic features for 1,622 utterances
- File names and references

❌ **We need**:
- Actual WAV audio files
- Location of audio files or download instructions

## Recommendation

Since prosodic features were already extracted (proving audio files exist), try:
1. **Check with the person/team who extracted the features** - they know where the audio files are
2. **Check the original MASAC corpus source** - may have download instructions
3. **Use existing features for preliminary analysis** while searching for audio files

