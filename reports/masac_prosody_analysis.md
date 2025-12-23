# MASAC Prosody Analysis Report
## Replication of Spanish-English CSW Prosody Findings

### Methodology
- **Corpus**: MASAC (Hindi-English)
- **Features**: 11 prosodic features (basic prosodic features)
  - **Note**: DisVoice 103 features unavailable due to scipy compatibility issues
  - Using existing prosodic features: pitch, intensity, voice quality
- **Statistical Test**: Independent t-tests (Welch's for unequal variances)
- **Multiple Comparisons Correction**: Benjamini-Hochberg FDR (α=0.05)
- **Effect Size**: Cohen's d
- **Comparisons**: CSW vs. monolingual Hindi, CSW vs. monolingual English

### Data Summary
- **Total utterances analyzed**: 11
- **Code-switched (CSW)**: 1,139 (70.2%)
- **Monolingual Hindi (HI)**: 317 (19.5%)
- **Monolingual English (EN)**: 166 (10.2%)

### Key Findings by Feature Category

#### CSW vs. Monolingual English
**Pitch Features**:
- Total: 4
- Significantly different: 2 (50.0%)
- Average |Cohen's d|: 0.373

**Energy Features**:
- Total: 4
- Significantly different: 3 (75.0%)
- Average |Cohen's d|: 0.425

**Voice_quality Features**:
- Total: 3
- Significantly different: 3 (100.0%)
- Average |Cohen's d|: 0.275

#### CSW vs. Monolingual Hindi
**Pitch Features**:
- Total: 4
- Significantly different: 1 (25.0%)
- Average |Cohen's d|: 0.360

**Energy Features**:
- Total: 4
- Significantly different: 2 (50.0%)
- Average |Cohen's d|: 0.247

**Voice_quality Features**:
- Total: 3
- Significantly different: 2 (66.7%)
- Average |Cohen's d|: 0.250

### Overall Results

- **CSW vs. EN**: 8 / 11 features (72.7%) significantly different
- **CSW vs. HI**: 5 / 11 features (45.5%) significantly different

### Comparison with Spanish-English Paper Findings

| Feature Category | Spanish-English | MASAC (CS vs EN) | MASAC (CS vs HI) | Pattern Match |
|----------------|-----------------|------------------|------------------|---------------|
| Duration | 96.0% | 0.0% | 0.0% | EN:✗ HI:✗ |
| Energy | 87.5% | 75.0% | 50.0% | EN:✓ HI:✗ |
| Pitch | 30.0% | 50.0% | 25.0% | EN:✗ HI:✓ |

### Top Significant Features (by |Cohen's d|)

#### CSW vs. Monolingual English
| Feature | Category | p (adjusted) | Cohen's d |
|---------|----------|--------------|-----------|
| maximum_intensity | energy | 0.0000 | 0.672 |
| mean_intensity | energy | 0.0002 | 0.408 |
| maximum_pitch | pitch | 0.0002 | 0.405 |
| hnr | voice_quality | 0.0432 | 0.212 |
| minimum_intensity | energy | 0.0130 | -0.196 |

#### CSW vs. Monolingual Hindi
| Feature | Category | p (adjusted) | Cohen's d |
|---------|----------|--------------|-----------|
| maximum_pitch | pitch | 0.0000 | 0.360 |
| maximum_intensity | energy | 0.0000 | 0.329 |
| hnr | voice_quality | 0.0016 | 0.242 |
| mean_intensity | energy | 0.0300 | 0.164 |
| jitter | voice_quality | 0.0043 | -0.259 |

### Summary

**Key Findings:**
1. CSW differs prosodically from monolingual English: 72.7% of features significant
2. CSW differs prosodically from monolingual Hindi: 45.5% of features significant
3. CSW shows **greater differences** from monolingual English than Hindi

**Limitations:**
- Analysis uses 11 basic prosodic features (not DisVoice 103 features)
- DisVoice extraction failed due to scipy compatibility issues
- Results should be interpreted as preliminary findings

**Next Steps:**
1. Resolve DisVoice scipy compatibility to extract full 103 features
2. Compare findings with DisVoice 103 features for full replication
3. Analyze speaker-level variation
4. Investigate language-specific effects