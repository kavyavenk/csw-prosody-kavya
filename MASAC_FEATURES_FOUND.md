# MASAC Features Found - Analysis Options

## What We Found

### ✅ Existing Prosodic Features File
**File**: `data/masac_raw/with acoustic-prosodic features.csv`

**Contents**:
- **1,622 utterances** with prosodic features already extracted
- **Language distribution**: CSW (1,139), HI (317), EN (166)
- **Prosodic features included**:
  - Pitch: Minimum, Maximum, Mean, Std Dev
  - Intensity: Minimum, Maximum, Mean, Std Dev  
  - Voice quality: Jitter, Shimmer, HNR

**Important Note**: These are **basic prosodic features**, NOT the DisVoice 103 features used in the Spanish-English paper.

### 📊 Model Results File
**File**: `MASAC_general_results.csv`

**Contents**:
- Model results from classification tasks
- Feature importance rankings
- Shows which prosodic features were most predictive

**Note**: This contains model results, not raw features or audio file paths.

## What This Means

### Good News ✅
1. **Audio files DO exist** - Features were extracted, so audio files must be available somewhere
2. **Prosodic features already extracted** - We have basic prosodic features for 1,622 utterances
3. **Language labels available** - CSW, HI, EN labels are present

### Limitations ⚠️
1. **Not DisVoice 103 features** - The Spanish-English paper specifically used DisVoice's 103 features
2. **Fewer features** - Only ~12 prosodic features vs. 103 in DisVoice
3. **Audio file location unknown** - We still don't know where the audio files are stored

## Analysis Options

### Option 1: Use Existing Features (Quick Analysis)
We can run a preliminary analysis using the existing prosodic features:

```python
# Adapt the analysis to use existing features
python scripts/04_first_contrasts.py --corpus masac --features-file data/masac_raw/with\ acoustic-prosodic\ features.csv
```

**Pros**: 
- Can run analysis immediately
- Tests if basic prosodic differences exist

**Cons**:
- Not exactly replicating Spanish-English methodology
- Fewer features = less comprehensive analysis

### Option 2: Find Audio Files and Extract DisVoice Features (Full Replication)
To fully replicate the Spanish-English paper, we need:
1. **Find audio files** (they exist since features were extracted)
2. **Extract DisVoice 103 features** using our pipeline
3. **Run full statistical analysis**

**Where to look for audio files**:
- Check if they're in a different directory
- Contact whoever extracted these features
- Check if there's a data sharing agreement or repository

### Option 3: Hybrid Approach
1. Use existing features for preliminary analysis
2. Search for audio files to extract DisVoice features
3. Compare results from both feature sets

## Next Steps

### Immediate (Using Existing Features)
1. Create a script to convert existing features to our format
2. Run statistical comparisons (CSW vs HI, CSW vs EN)
3. Generate preliminary report

### To Find Audio Files
1. Check if audio files are in a different location
2. Search for references to audio file paths in the data
3. Contact the person/team who extracted these features

### To Extract DisVoice Features (Full Replication)
Once audio files are found:
```bash
python scripts/12_run_masac_prosody_analysis.py
```

## Recommendation

**Start with Option 1** - Use existing features for a preliminary analysis to:
- Test if prosodic differences exist in MASAC
- Validate the analysis pipeline
- Generate initial results

Then **pursue Option 2** - Find audio files and extract DisVoice features for full replication.

