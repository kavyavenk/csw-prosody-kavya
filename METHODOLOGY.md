# Spanish-English Code-Switching Prosody: Methods and Findings

## Paper Overview

**Title:** "The Sound of Code-Switching: Prosodic Signatures of Spanish-English Speech"

This paper investigates whether code-switched (CSW) utterances differ prosodically from monolingual speech in spontaneous conversation, and how speaker proficiency and multilingual features influence this variation.

## Research Questions

1. **RQ1:** Is there utterance-level variation across a suite of language-independent pitch, energy, and duration features between code-switched and monolingual spontaneous speech?
2. **RQ2:** How is this variation influenced by speaker proficiency and/or specifically multilingual features of speech?

## Corpus

- **Bangor Miami (BM) Corpus**: 35 hours of spontaneous Spanish-English dialogue
  - 56 conversations
  - 46,900+ transcribed utterances
  - 84 speakers (52 female, 32 male)
  - Mix of monolingual English, monolingual Spanish, and code-switched Spanish-English
  - Token-level language identification (LID) tags
  - Demographic information: medium of schooling, years of language experience, self-reported ability, age, parents' primary language

## Feature Extraction

### DisVoice Prosodic Features
- **103 utterance-level prosodic features** extracted using DisVoice
- **Three feature categories:**
  1. **Fundamental Frequency (F0/Pitch)**: Mean, min, max, std dev, range, z-scores
  2. **Energy/Intensity**: Mean, min, max, std dev, z-scores
  3. **Duration**: Segment durations, speaking rate, pause patterns
- **Six functionals** applied across voiced and unvoiced segments
- Features extracted from denoised audio data

### Code-Switching Indices
- **M-index**: Quantifies CSW quantity at utterance level
- **I-index**: Quantifies CSW frequency
- **Direction**: en→es vs. es→en
- **Strategy**: Insertional vs. Alternational

## Statistical Methods

### 1. Feature-Level Comparisons
- **Independent t-tests** comparing CSW vs. monolingual distributions
- **Benjamini-Hochberg (BH) FDR correction** for multiple comparisons (α=0.05)
- **Cohen's d** effect sizes (interpretation: small ~0.2, medium ~0.5, large ~0.8)
- Comparisons made:
  - CSW vs. monolingual English
  - CSW vs. monolingual Spanish
  - CSW vs. combined monolingual (EN + ES)

### 2. Modeling
- **Unsupervised**: k-means clustering (scikit-learn) to group prosodic patterns
- **Supervised**: Whisper-base prosodic-LID model evaluation
  - Binary classification (English vs. Spanish)
  - Off-the-shelf and fine-tuned performance
  - 90/10 speaker-level train/test split

### 3. Mixed-Effects Modeling
- Speaker proficiency as random/fixed effects
- Controls for speaker variables and demographic factors

## Key Findings

### 1. CSW Differs Prosodically from Monolingual Speech

**Main Result**: The majority of prosodic features in code-switched utterances are significantly different (p < 0.05) from monolingual speech in both English and Spanish.

**Feature Category Importance:**
- **Duration features**: ~96% differ significantly from monolingual
- **Energy features**: ~87.5% differ significantly
- **Pitch features**: Up to 30% similar to monolingual (least affected)

**Qualitative Patterns:**
- **F0/Pitch**: 
  - Initial and final voiced segments have **higher mean F0** in CSW
  - **Greater F0 variation** in CSW, especially for initial segments
  - Consistently **greater differences** between CSW and Spanish than CSW and English
  
- **Energy**:
  - Initial and final voiced segments have **lower energy** in CSW
  
- **Overall**: CSW prosody is **more similar to monolingual Spanish than English** in this corpus

### 2. Speaker Proficiency Effects

- Speaker-specific factors (proficiency indicators) explain significant variation
- Variation modulated by speaker language dominance and proficiency levels

### 3. Model Performance

- Prosodic differences are **salient enough to be learned** by:
  - Unsupervised clustering models
  - End-to-end predictive LID models (Whisper)
- Demonstrates that prosodic variation is quantifiable and learnable

## Replication Strategy

### For SEAME (Mandarin-English) and MASAC (Hindi-English)

1. **Feature Extraction**:
   - Use DisVoice to extract same 103 prosodic features
   - Ensure 16kHz mono WAV format
   - Utterance-level segmentation based on timestamps/LID

2. **Data Preparation**:
   - Build manifests with: utt_id, file_id, wav_path, start_sec, end_sec, speaker, lang, condition
   - Language labels: EN, ZH (SEAME) or HI (MASAC), CS
   - Condition labels: monolingual_EN, monolingual_ZH/HI, code_switched

3. **Statistical Analysis**:
   - Independent t-tests (Welch's t-test for unequal variances)
   - Benjamini-Hochberg FDR correction
   - Cohen's d effect sizes
   - Compare: CS vs. monolingual_EN, CS vs. monolingual_ZH/HI

4. **Pilot Testing**:
   - Start with balanced subsets (e.g., 100-500 utterances per condition)
   - Ensure speaker balance across conditions
   - Verify audio quality and alignment

5. **Extended Analysis**:
   - Mixed-effects models with speaker as random effect
   - Proficiency analysis (if metadata available)
   - CSW direction and strategy effects

## Expected Outcomes

- **Cross-linguistic validation**: Test if duration > energy > pitch pattern generalizes
- **Language-specific effects**: Compare tonal (Mandarin) vs. non-tonal (Hindi, Spanish) effects
- **Speaker factors**: Examine how proficiency modulates prosodic differences

## References

- DisVoice: https://disvoice.readthedocs.io/en/latest/Prosody.html
- Benjamini-Hochberg correction: Controls false discovery rate in multiple comparisons
- Cohen's d: Standardized effect size measure

