# Research Recommendations: Next Steps for Code-Switched Multilingual Speech

## Summary of Implemented Analysis Pipeline

We've implemented a comprehensive analysis pipeline for investigating functional anchors and advanced modeling in code-switched speech prosody:

### ✅ Completed Implementation

1. **Discourse Markers & Repetitions Detection** (`scripts/16_detect_discourse_markers_repetitions.py`)
   - Detects discourse markers in English, Mandarin, and Hindi
   - Identifies word repetitions within utterances
   - Marks discourse markers near code-switch boundaries

2. **Switch Directionality Extraction** (`scripts/17_extract_switch_directionality.py`)
   - Extracts EN→ZH vs ZH→EN (or EN→HI vs HI→EN) patterns
   - Classifies switches as insertional vs alternational
   - Identifies first switch direction

3. **Mixed-Effects Modeling** (`scripts/18_mixed_effects_analysis.py`)
   - Builds mixed-effects models with speaker/conversation random effects
   - Includes functional anchors and directionality as predictors
   - Provides model comparison and statistical reporting

4. **Feature Integration** (`scripts/19_integrate_features_for_analysis.py`)
   - Combines prosodic features with annotations
   - Creates interaction terms for analysis
   - Produces analysis-ready dataset

5. **Report Generation** (`scripts/20_generate_functional_anchors_report.py`)
   - Generates comprehensive analysis reports
   - Compares prosodic differences with/without functional anchors
   - Provides statistical summaries

6. **Master Pipeline** (`scripts/21_run_functional_anchors_pipeline.py`)
   - Runs complete pipeline end-to-end
   - Handles errors gracefully
   - Produces all outputs in organized directory structure

## Novel Contributions for Publication

### 1. Function-Conditional Prosody in CSW (High Novelty)

**Research Question**: Do discourse markers and repetitions explain prosodic variation in CSW?

**Hypothesis**: Prosodic differences between CSW and monolingual speech are larger when functional anchors (discourse markers, repetitions) are present near switch boundaries.

**Why it's novel:**
- Moves beyond "CSW differs from monolingual" to "when and why"
- Provides functional explanation for duration dominance
- Cross-linguistic validation across language families

**Analysis Approach:**
- Stratify CSW vs monolingual comparisons by presence/absence of functional anchors
- Test if prosodic differences are modulated by anchor presence
- Compare CSW utterances with vs without anchors

**Expected Findings:**
- Discourse markers near switches show stronger prosodic differences
- Repetitions may correlate with boundary-like prosody (lengthening, pauses)
- Duration features show strongest anchor effects (consistent with prior findings)

**Publication Potential**: High - addresses "why" question, provides mechanistic explanation

### 2. Directional Effects in Code-Switching (Medium-High Novelty)

**Research Question**: Do EN→L1 switches differ prosodically from L1→EN switches?

**Hypothesis**: Switch direction matters - L1→L2 switches may show different prosodic patterns than L2→L1 switches.

**Why it's novel:**
- Most CSW prosody studies don't analyze directionality
- Directional asymmetry could reveal language dominance effects
- Cross-linguistic comparison (Mandarin vs Hindi) tests generalization

**Analysis Approach:**
- Extract switch direction from word-level LID tags
- Compare prosodic features between L1→L2 and L2→L1 switches
- Test interaction with functional anchors

**Expected Findings:**
- Directional differences may be language-pair specific
- Mandarin (tonal) may show different patterns than Hindi (non-tonal)
- Interaction with discourse markers may differ by direction

**Publication Potential**: Medium-High - depends on strength of effects

### 3. Mixed-Effects Modeling of CSW Prosody (Medium Novelty)

**Research Question**: How much variation is explained by speaker vs utterance-level factors?

**Why it's novel:**
- Upgrades from simple t-tests to proper statistical modeling
- Controls for speaker and conversation effects
- Tests multiple predictors simultaneously

**Analysis Approach:**
- Build mixed-effects models with speaker/conversation as random effects
- Include condition, functional anchors, directionality as fixed effects
- Compare model fits and effect sizes

**Expected Findings:**
- Speaker effects explain significant variation
- Functional anchors remain significant after controlling for speaker
- Model comparison reveals best predictors

**Publication Potential**: Medium - methodological contribution, but less novel than functional anchors

## Recommended Next Steps

### Immediate (Next 1-2 weeks)

1. **Run Pipeline on Existing Data**
   ```bash
   # Test on SEAME
   python scripts/21_run_functional_anchors_pipeline.py \
       --corpus seame \
       --manifest manifests/seame_manifest.csv \
       --features features/seame_disvoice_utt.csv
   
   # Test on MASAC
   python scripts/21_run_functional_anchors_pipeline.py \
       --corpus masac \
       --manifest manifests/masac_manifest.csv \
       --features features/masac_disvoice_utt.csv \
       --words data/masac_raw/masac_words_sample.csv
   ```

2. **Validate Discourse Marker Detection**
   - Manually check a sample of detected markers
   - Refine marker lists based on corpus-specific patterns
   - Add corpus-specific markers if needed

3. **Preliminary Analysis**
   - Review functional anchors report
   - Identify strongest effects
   - Determine which features show anchor modulation

### Short-term (Next 1-2 months)

#### 1. Intonation Unit Boundaries Analysis

**Goal**: Analyze prosodic boundaries using TextGrid data

**Approach**:
- Extract intonation unit boundaries from TextGrid files
- Measure pause duration, pitch reset at boundaries
- Compare boundary prosody in CSW vs monolingual
- Test if boundaries align with code-switch points

**Implementation**:
- Use existing TextGrid parsing code (`data/SEAME/PyToBI/`)
- Extract boundary features (pause duration, F0 reset, etc.)
- Add to analysis pipeline

**Novelty**: High - boundary analysis is understudied in CSW

#### 2. Language Family Comparison

**Goal**: Compare patterns across tonal (Mandarin) vs non-tonal (Hindi, Spanish) languages

**Approach**:
- Run same analyses on all three language pairs
- Compare effect sizes across languages
- Test if tonal languages show different patterns

**Expected Findings**:
- Duration effects may be universal
- Pitch effects may differ by tonal vs non-tonal
- Functional anchors may show language-specific patterns

**Novelty**: High - cross-linguistic comparison is valuable

#### 3. Pre-annotated Data Integration

**Goal**: Leverage any pre-annotated discourse markers or boundaries

**Approach**:
- Check if SEAME/MASAC have pre-annotated discourse markers
- Integrate with detected markers
- Use as gold standard for validation

**Novelty**: Medium - improves accuracy

### Medium-term (Next 3-6 months)

#### 1. Naturalness in Multilingual Speech Generation

**Goal**: Apply findings to improve multilingual speech synthesis

**Research Questions**:
- Do current TTS systems produce natural code-switched prosody?
- Can prosodic patterns predict perceived naturalness?
- How do functional anchors affect naturalness ratings?

**Approach**:
- Collect or generate CSW speech samples
- Extract prosodic features
- Obtain naturalness ratings (MOS, pairwise comparisons)
- Build models predicting naturalness from prosody
- Test if adding functional anchor information improves predictions

**Novelty**: Very High - bridges production and perception, practical application

**Implementation Steps**:
1. Generate CSW speech samples using TTS systems
2. Extract prosodic features (same pipeline)
3. Collect naturalness ratings (crowdsourcing or lab study)
4. Build regression models: `naturalness ~ prosodic_features + functional_anchors`
5. Compare model performance with/without functional anchors

**Expected Contributions**:
- Identify prosodic features that predict naturalness
- Show functional anchors improve naturalness prediction
- Provide guidelines for CSW TTS system design

#### 2. Mixed Effects with Proficiency

**Goal**: Incorporate speaker proficiency into models

**Approach**:
- Extract proficiency indicators from metadata
- Add proficiency as predictor to mixed-effects models
- Test interactions: proficiency × condition × functional anchors

**Novelty**: Medium - extends existing RQ2 from original paper

#### 3. Table/Summary Analysis

**Goal**: Create comprehensive comparison tables across language pairs

**Approach**:
- Generate standardized tables comparing:
  - Feature significance rates
  - Effect sizes
  - Functional anchor effects
  - Directional effects
- Include statistical tests for cross-linguistic differences

**Novelty**: Medium - synthesis contribution

## Publication Strategy

### Paper 1: Functional Anchors (Target: Interspeech, ACL, or Phonetics journal)

**Title**: "Functional Anchors in Code-Switched Speech: How Discourse Markers and Repetitions Modulate Prosodic Differences"

**Key Contributions**:
- Function-conditional prosody in CSW
- Cross-linguistic validation (Mandarin-English, Hindi-English)
- Explanation for duration dominance

**Timeline**: 2-3 months (after running pipeline and analyzing results)

### Paper 2: Naturalness in Generation (Target: Interspeech, ICASSP, or TTS workshop)

**Title**: "Predicting Naturalness in Code-Switched Speech Synthesis: The Role of Prosodic Functional Anchors"

**Key Contributions**:
- Naturalness prediction models
- Functional anchors improve prediction
- Guidelines for CSW TTS

**Timeline**: 4-6 months (requires data collection)

### Paper 3: Cross-Linguistic Comparison (Target: Language and Speech, JPhon)

**Title**: "Cross-Linguistic Prosodic Patterns in Code-Switching: Tonal vs Non-Tonal Languages"

**Key Contributions**:
- Comparison across language families
- Tonal vs non-tonal differences
- Universal vs language-specific patterns

**Timeline**: 3-4 months (after completing all analyses)

## Data Requirements

### For Naturalness Study:
- CSW speech samples (synthetic or natural)
- Naturalness ratings (MOS scale or pairwise)
- Speaker metadata (if available)

### For Intonation Unit Boundaries:
- TextGrid files with boundary annotations
- Pause and pitch measurements at boundaries

### For Proficiency Analysis:
- Speaker proficiency indicators
- Language dominance measures
- Demographic information

## Tools and Resources

### Existing Tools:
- DisVoice: Prosodic feature extraction ✅
- TextGrid parsing: PyToBI code available ✅
- Statistical modeling: statsmodels, scipy ✅

### Needed Tools:
- Naturalness rating collection: Prolific, MTurk, or lab study
- TTS system for generation: Coqui TTS, VITS, or similar
- Boundary detection: Praat scripts or MFA alignment

## Success Metrics

### For Functional Anchors Paper:
- Significant modulation by discourse markers in ≥30% of features
- Effect sizes (Cohen's d) > 0.2 for anchor effects
- Consistent patterns across language pairs

### For Naturalness Paper:
- R² > 0.3 for naturalness prediction
- Functional anchors improve prediction by ≥5% R²
- Significant correlation with human ratings

### For Cross-Linguistic Paper:
- Significant differences between language pairs
- Universal patterns identified (duration effects)
- Language-specific patterns identified (pitch effects)

## Next Actions

1. ✅ **Run pipeline on existing data** (this week)
2. ⏳ **Review results and refine analyses** (next week)
3. ⏳ **Plan naturalness study** (next 2 weeks)
4. ⏳ **Extract intonation unit boundaries** (next month)
5. ⏳ **Begin writing functional anchors paper** (next month)
