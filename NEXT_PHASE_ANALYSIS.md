# Next Phase Analysis: Functional Anchors and Advanced Modeling

This document describes the next-phase analysis pipeline for code-switched multilingual speech prosody research.

## Overview

Building on the replication findings that CSW differs prosodically from monolingual speech, this phase investigates:

1. **Functional Anchors**: How discourse markers and repetitions modulate prosodic differences
2. **Switch Directionality**: Whether EN→L1 vs L1→EN switches show different prosodic patterns
3. **Mixed-Effects Modeling**: Statistical models that control for speaker and conversation effects
4. **Cross-Linguistic Comparison**: Comparing patterns across language families

## Research Questions

### RQ3: Function-Dependent Prosody
- Do discourse markers and repetitions explain part of the prosodic variation in CSW?
- Are prosodic differences larger/smaller when functional anchors are present?

### RQ4: Directional Effects
- Do EN→L1 switches differ prosodically from L1→EN switches?
- Does switch direction interact with prosodic features?

### RQ5: Speaker and Context Effects
- How much variation is explained by speaker-level factors vs. utterance-level factors?
- Do mixed-effects models reveal different patterns than simple t-tests?

## Pipeline Overview

```
1. Detect Discourse Markers & Repetitions
   └─> scripts/16_detect_discourse_markers_repetitions.py
   
2. Extract Switch Directionality
   └─> scripts/17_extract_switch_directionality.py
   
3. Integrate Features
   └─> scripts/19_integrate_features_for_analysis.py
   
4. Mixed-Effects Modeling
   └─> scripts/18_mixed_effects_analysis.py
   
5. Generate Reports
   └─> scripts/20_generate_functional_anchors_report.py
```

## Usage

### Quick Start: Run Complete Pipeline

```bash
# For SEAME
python scripts/21_run_functional_anchors_pipeline.py \
    --corpus seame \
    --manifest manifests/seame_manifest.csv \
    --features features/seame_disvoice_utt.csv \
    --output-dir results/functional_anchors/seame

# For MASAC (with word-level data)
python scripts/21_run_functional_anchors_pipeline.py \
    --corpus masac \
    --manifest manifests/masac_manifest.csv \
    --features features/masac_disvoice_utt.csv \
    --words data/masac_raw/masac_words_sample.csv \
    --output-dir results/functional_anchors/masac
```

### Step-by-Step Execution

#### Step 1: Detect Discourse Markers and Repetitions

```bash
python scripts/16_detect_discourse_markers_repetitions.py \
    --manifest manifests/seame_manifest.csv \
    --output results/seame_manifest_with_anchors.csv \
    --corpus seame
```

**Output columns added:**
- `has_discourse_marker`: Boolean
- `discourse_marker_type`: Type (filler/connector/reformulation/emphasis)
- `n_discourse_markers`: Count
- `has_repetition`: Boolean
- `n_repetitions`: Count
- `has_discourse_marker_near_switch`: Boolean (CSW only)

#### Step 2: Extract Switch Directionality

```bash
python scripts/17_extract_switch_directionality.py \
    --manifest results/seame_manifest_with_anchors.csv \
    --output results/seame_manifest_with_direction.csv \
    --corpus seame
```

**Output columns added:**
- `switch_direction`: List of switch directions (e.g., "EN→ZH,ZH→EN")
- `first_switch_direction`: First switch direction
- `n_switches`: Number of switches
- `switch_type`: "insertional" or "alternational"
- `switch_direction_class`: "L1→L2" or "L2→L1"

#### Step 3: Integrate All Features

```bash
python scripts/19_integrate_features_for_analysis.py \
    --features features/seame_disvoice_utt.csv \
    --manifest results/seame_manifest_with_direction.csv \
    --output results/seame_integrated_features.csv \
    --corpus seame
```

**Creates analysis-ready dataset with:**
- All prosodic features
- Functional anchor indicators
- Switch directionality
- Interaction terms (e.g., `csw_x_dm`)

#### Step 4: Mixed-Effects Modeling

```bash
python scripts/18_mixed_effects_analysis.py \
    --features features/seame_disvoice_utt.csv \
    --manifest results/seame_manifest_with_direction.csv \
    --output-dir results/mixed_effects/seame \
    --corpus seame \
    --n-features 10
```

**Outputs:**
- `{corpus}_mixed_effects_comparison.csv`: Model comparison table
- `{corpus}_mixed_effects_results.txt`: Detailed model summaries

#### Step 5: Generate Report

```bash
python scripts/20_generate_functional_anchors_report.py \
    --integrated results/seame_integrated_features.csv \
    --output reports/seame_functional_anchors_report.md \
    --corpus seame
```

## Discourse Markers

### English
- **Fillers**: um, uh, er, ah, eh
- **Connectors**: like, you know, so, well, actually, basically
- **Reformulation**: I mean, like, you know, sort of, kind of
- **Emphasis**: really, actually, literally, basically

### Mandarin (ZH)
- **Fillers**: 呃, 嗯, 啊, 那个, 这个
- **Connectors**: 然后, 所以, 但是, 可是, 不过, 而且
- **Reformulation**: 就是, 那个, 这个
- **Emphasis**: 真的, 其实, 就是

### Hindi (HI)
- **Fillers**: um, uh, er, ah, eh, hmm
- **Connectors**: toh, phir, lekin, par, aur, ya, ki
- **Reformulation**: matlab, yani, jaise
- **Emphasis**: bilkul, sach mein, asli mein

## Analysis Approach

### Functional Anchors Analysis

For each prosodic feature, compare:
1. **CSW vs Monolingual WITH discourse marker/repetition**
2. **CSW vs Monolingual WITHOUT discourse marker/repetition**
3. **CSW with anchor vs CSW without anchor**

This reveals whether functional anchors modulate prosodic differences.

### Mixed-Effects Models

Model structure:
```
feature ~ condition + has_discourse_marker + has_repetition + 
          switch_direction_class + (1|speaker) + (1|conversation)
```

Where:
- `condition`: CSW vs monolingual
- `has_discourse_marker`: Binary indicator
- `has_repetition`: Binary indicator
- `switch_direction_class`: L1→L2 vs L2→L1 (CSW only)
- Random effects: Speaker and conversation

## Expected Contributions

1. **Function-Conditional Prosody**: Show that prosodic differences are modulated by discourse function
2. **Directional Effects**: Demonstrate that switch direction matters for prosody
3. **Statistical Rigor**: Upgrade from t-tests to mixed-effects models
4. **Cross-Linguistic Validation**: Compare patterns across language families

## Output Files

After running the pipeline, you'll have:

```
results/functional_anchors/{corpus}/
├── {corpus}_manifest_with_anchors.csv
├── {corpus}_manifest_with_direction.csv
├── {corpus}_integrated_features.csv
├── {corpus}_functional_anchors_report.md
└── mixed_effects/
    ├── {corpus}_mixed_effects_comparison.csv
    └── {corpus}_mixed_effects_results.txt
```

## Next Steps

1. **Intonation Unit Boundaries**: Analyze prosodic boundaries using TextGrid data
2. **Language Family Comparison**: Compare patterns across tonal (Mandarin) vs non-tonal (Hindi, Spanish) languages
3. **Naturalness in Generation**: Apply findings to improve multilingual speech synthesis
4. **Pre-annotated Data**: Leverage any pre-annotated discourse markers or boundaries

## References

- Discourse markers in code-switching: [relevant citations]
- Mixed-effects modeling: Bates et al. (2015) "Fitting Linear Mixed-Effects Models"
- Functional anchors: [relevant citations]
