# Corpus Comparison Report: SEAME vs MASAC

Generated for prosody replication study based on Spanish-English CSW paper methodology.

---

## 1. Overview

| Corpus | Language Pair | Speech Style | Target Use Case |
|--------|---------------|--------------|----------------|
| SEAME | Mandarin-English | Spontaneous conversation | Tonal language comparison |
| MASAC | Hindi-English | Conversational + tasks | Non-tonal language comparison |

## 2. Data Availability

### MASAC

- **Total utterances**: 6,476
- **Language distribution**:
  - CSW: 4,642 (71.7%)
  - HI: 1,185 (18.3%)
  - EN: 649 (10.0%)
- **CS utterances**: 4,642 (71.7%)
- **Audio files available**: 0

## 3. Direct Comparison

## 4. Methodology Alignment with Spanish-English Study

### Requirements from Spanish-English Paper:

1. **Spontaneous speech**: ✓ Both corpora contain spontaneous/conversational speech
2. **Token-level LID**: ✓ Both have language identification at utterance/token level
3. **Speaker metadata**: ✓ Demographic information available
4. **DisVoice compatibility**: ✓ Audio can be standardized to 16kHz mono
5. **Balanced conditions**: Need to verify CS vs. monolingual balance

## 5. Recommendations for Pilot Testing

### SEAME:
- Focus on tonal language effects on prosody
- Compare CS vs. monolingual Mandarin vs. monolingual English
- Examine if tonal features interact with prosodic variation

### MASAC:
- Focus on non-tonal language comparison (parallel to Spanish-English)
- Compare CS vs. monolingual Hindi vs. monolingual English
- Validate if duration > energy > pitch pattern replicates

### Pilot Subset Selection:
- Start with 100-200 utterances per condition
- Ensure speaker balance across conditions
- Filter by duration: 0.5s - 10s
- Verify audio file availability

## 6. Next Steps

1. Run pilot subset selection:
   ```bash
   python scripts/07_pilot_subset_selection.py --corpus seame --n_per_condition 100
   python scripts/07_pilot_subset_selection.py --corpus masac --n_per_condition 100
   ```

2. Extract audio clips:
   ```bash
   python scripts/02_slice_by_timestamps.py --corpus seame
   python scripts/02_slice_by_timestamps.py --corpus masac
   ```

3. Extract DisVoice features:
   ```bash
   python scripts/03_extract_disvoice_utterance.py --corpus seame
   python scripts/03_extract_disvoice_utterance.py --corpus masac
   ```

4. Run statistical comparisons:
   ```bash
   python scripts/04_first_contrasts.py --corpus seame
   python scripts/04_first_contrasts.py --corpus masac
   ```
