# Comprehensive Summary: Mixed-Effects Modeling and Analysis Decisions

## Executive Summary

This document summarizes all completed work, design decisions, and next steps for the code-switched multilingual speech prosody research project. All choices are documented with clear reasoning based on statistical best practices and prosody research literature.

## ✅ Completed Work

### 1. Discourse Markers and Repetitions Detection
**Status**: ✅ Complete and tested

**Implementation**: `scripts/16_detect_discourse_markers_repetitions.py`

**Key Features**:
- Detects discourse markers in English, Mandarin, and Hindi
- Identifies word repetitions within utterances
- Marks discourse markers near code-switch boundaries

**Results**:
- **SEAME**: 10/10 features show DM modulation (100%)
- **MASAC**: 2/10 features show DM modulation (20%)
- **Repetitions**: Moderate effects in both corpora

**Rationale**: Functional anchors hypothesis - discourse markers and repetitions may explain when and why CSW differs prosodically from monolingual speech.

### 2. Switch Directionality Extraction
**Status**: ✅ Complete and tested

**Implementation**: `scripts/17_extract_switch_directionality.py`

**Key Features**:
- Extracts EN→ZH vs ZH→EN (or EN→HI vs HI→EN) patterns
- Classifies switches as insertional vs alternational
- Identifies first switch direction

**Results (MASAC)**:
- L1→L2: 62.2% of CSW utterances
- L2→L1: 37.8% of CSW utterances
- Alternational: 60.7%
- Insertional: 39.3%

**Rationale**: Directional asymmetry may reveal language dominance effects and modulate prosodic patterns differently.

### 3. Enhanced Mixed-Effects Modeling Framework
**Status**: ✅ Complete (pilot tested)

**Implementation**: `scripts/23_enhanced_mixed_effects.py`

**Key Features**:
- ✅ Toggle for random effects (speaker, conversation, both, or none)
- ✅ Distribution checks for linear vs nonlinear modeling
- ✅ Interaction terms (discourse markers × directionality)
- ✅ Pilot testing on balanced subsets
- ✅ Model comparison (AIC, BIC)

**Design Decisions** (see `MODELING_DECISIONS.md` for details):

#### Random Effects Structure
**Choice**: `(1|speaker) + (1|conversation)`
**Rationale**: 
- Accounts for speaker-level variation (voice quality, speaking rate)
- Accounts for conversation-level variation (topic, context, interaction dynamics)
- Standard hierarchical structure in prosody research

**Toggle**: Yes - can disable to compare with OLS models

#### Fixed Effects
**Choice**: `condition + has_discourse_marker + has_repetition + is_l1_to_l2`
**Rationale**:
- Addresses all research questions simultaneously
- Binary encoding for simplicity and interpretability
- Directionality only applies to CSW utterances (NaN for monolingual)

#### Interaction Terms
**Choice**: Key interactions only
- `condition × has_discourse_marker`: Tests if DM effect differs between CSW and monolingual
- `has_discourse_marker × is_l1_to_l2`: Tests if DM effect differs by switch direction
- `condition × is_l1_to_l2`: Tests if directionality matters only in CSW context

**Rationale**: Balance between theory-driven interactions and model parsimony

#### Linear vs Nonlinear
**Choice**: Start with linear, check distributions
**Rationale**:
- Linear models are standard in prosody research
- Distribution checks inform whether transformations are needed
- Nonlinear models only if strongly non-normal and theory suggests nonlinearity

**Implementation**: Automatic distribution checks with recommendations

### 4. Discourse Markers × Directionality Interrelation Analysis
**Status**: ✅ Complete

**Implementation**: `scripts/24_analyze_dm_directionality_interrelation.py`

**Key Features**:
- Chi-square test for association between DMs and switch direction
- Cramér's V for effect size
- Prosodic modulation analysis by DM × Direction
- Interaction effect testing

**Rationale**: Tests whether discourse markers are more likely with certain switch directions and whether they modulate prosody differently by direction.

### 5. Feature Integration
**Status**: ✅ Complete

**Implementation**: `scripts/19_integrate_features_for_analysis.py`

**Key Features**:
- Combines prosodic features with annotations
- Creates interaction terms
- Produces analysis-ready dataset

### 6. Report Generation
**Status**: ✅ Complete

**Implementation**: `scripts/20_generate_functional_anchors_report.py`

**Outputs**:
- Functional anchors analysis reports
- Statistical summaries
- Cross-corpus comparisons

## 📊 Current Results Summary

### SEAME (Mandarin-English)
- **Total utterances**: 52,313
- **CSW utterances**: 30,292 (57.9%)
- **Discourse markers**: 10/10 features modulated (100%)
- **Repetitions**: 7/10 features modulated (70%)

### MASAC (Hindi-English)
- **Total utterances**: 6,476
- **CSW utterances**: 4,642 (71.7%)
- **Discourse markers**: 2/10 features modulated (20%)
- **Repetitions**: 5/10 features modulated (50%)
- **Directionality**: L1→L2 (62.2%) vs L2→L1 (37.8%)

## 🎯 Key Design Decisions with Reasoning

### 1. Random Effects: Hierarchical Structure
**Decision**: Speaker + Conversation as random effects
**Reasoning**: 
- Accounts for known sources of variation in prosody
- Standard approach in psycholinguistics and prosody research
- Allows generalization beyond specific speakers/conversations

### 2. Feature Selection: Duration Priority
**Decision**: Prioritize Duration > Energy > Pitch features
**Reasoning**:
- Based on prior findings: Duration (96% significant) > Energy (87.5%) > Pitch (~30%)
- Variance-based selection within categories
- Ensures representation across feature types

### 3. Encoding: Binary for Functional Anchors
**Decision**: Binary (0/1) for discourse markers and repetitions
**Reasoning**:
- Simpler than counts or continuous measures
- Focuses on presence/absence effect
- More interpretable coefficients
- Can be extended to counts if needed

### 4. Model Type: Linear with Distribution Checks
**Decision**: Start with linear, check distributions, transform if needed
**Reasoning**:
- Linear models are standard in prosody research
- Distribution checks inform transformations
- Nonlinear models only if necessary and theoretically motivated

### 5. Pilot Testing: Balanced Subsets
**Decision**: Test on 500-utterance balanced subsets first
**Reasoning**:
- Faster iteration
- Catch issues early
- Validate methodology before full analysis
- ~10% of corpus size - large enough for stability

## ⚠️ Known Issues and Solutions

### 1. Mixed-Effects Model Convergence
**Issue**: Some models fail with "Singular matrix" errors
**Cause**: 
- Perfect collinearity in predictors
- Insufficient variation in random effects
- Small sample sizes in pilot tests

**Solutions**:
- ✅ Distribution checks identify problematic features
- ✅ Toggle for random effects allows comparison
- ✅ Pilot testing catches issues early
- ⏳ Consider simpler models if convergence fails
- ⏳ Use regularization if needed

### 2. Feature Distribution Non-Normality
**Issue**: Some features show strong non-normality
**Solution**: 
- ✅ Automatic distribution checks
- ✅ Recommendations for transformations
- ⏳ Implement log/sqrt transformations if needed
- ⏳ Consider nonlinear models for strongly non-normal features

## 📋 Next Steps

### Immediate (This Week)
1. ✅ **Run pilot tests** - COMPLETED
2. ✅ **Analyze DM × Directionality interrelation** - COMPLETED
3. ⏳ **Review pilot results** - Review convergence issues
4. ⏳ **Refine models** - Address singular matrix errors

### Short-term (Next 2 Weeks)
1. **Full dataset analysis**
   - Run enhanced mixed-effects models on full datasets
   - Compare with pilot results
   - Generate comprehensive reports

2. **Model refinement**
   - Address convergence issues
   - Test alternative random effects structures
   - Consider transformations for non-normal features

3. **Cross-corpus comparison**
   - Compare SEAME vs MASAC findings
   - Test language-family effects (tonal vs non-tonal)
   - Generate comparison report

### Medium-term (Next Month)
1. **Naturalness in Generation**
   - Frame research questions
   - Design naturalness measurement approach
   - Plan data collection/experiment

2. **Paper preparation**
   - Write methods section
   - Prepare figures and tables
   - Draft results section

## 🔬 Naturalness in Multilingual Speech Generation

### Research Questions (Scoping)
1. **Do current TTS systems produce natural code-switched prosody?**
   - Compare synthetic CSW prosody to natural CSW prosody
   - Identify prosodic features that differ

2. **Can prosodic patterns predict perceived naturalness?**
   - Collect naturalness ratings for CSW speech
   - Build models: `naturalness ~ prosodic_features + functional_anchors`
   - Test if functional anchors improve prediction

3. **How do functional anchors affect naturalness?**
   - Do discourse markers improve perceived naturalness?
   - Does switch direction affect naturalness?
   - Interaction effects?

### Measurement Approaches
1. **Subjective ratings**
   - Mean Opinion Score (MOS) scale
   - Pairwise comparisons
   - Crowdsourcing or lab study

2. **Objective measures**
   - Prosodic feature distances from natural speech
   - Functional anchor presence/absence
   - Switch direction patterns

3. **Hybrid approach**
   - Combine subjective and objective measures
   - Weighted naturalness score

### Implementation Plan
1. **Data collection**
   - Generate CSW speech samples using TTS systems
   - Collect naturalness ratings
   - Extract prosodic features (same pipeline)

2. **Analysis**
   - Build regression models: `naturalness ~ prosody + anchors`
   - Compare models with/without functional anchors
   - Test interaction effects

3. **Application**
   - Provide guidelines for CSW TTS system design
   - Identify prosodic features to prioritize
   - Recommend functional anchor handling

## 📚 Documentation

### Created Documents
1. **MODELING_DECISIONS.md** - Detailed design decisions and rationale
2. **NEXT_PHASE_ANALYSIS.md** - Pipeline overview and usage
3. **RESEARCH_RECOMMENDATIONS.md** - Publication strategy and contributions
4. **PIPELINE_STATUS.md** - Current status and validation
5. **COMPREHENSIVE_SUMMARY.md** - This document

### Scripts Created
1. `16_detect_discourse_markers_repetitions.py` - DM and repetition detection
2. `17_extract_switch_directionality.py` - Directionality extraction
3. `18_mixed_effects_analysis.py` - Basic mixed-effects modeling
4. `19_integrate_features_for_analysis.py` - Feature integration
5. `20_generate_functional_anchors_report.py` - Report generation
6. `21_run_functional_anchors_pipeline.py` - Master pipeline
7. `22_validate_pipeline.py` - Validation script
8. `23_enhanced_mixed_effects.py` - Enhanced modeling with options
9. `24_analyze_dm_directionality_interrelation.py` - Interrelation analysis

## ✅ Validation Status

### Pipeline Validation
- ✅ All scripts present and executable
- ✅ Input files validated
- ✅ Output files generated correctly
- ✅ Data integrity checks passed

### Analysis Validation
- ✅ SEAME analysis complete
- ✅ MASAC analysis complete
- ✅ Cross-corpus comparison possible
- ⚠️ Mixed-effects models need refinement (convergence issues)

## 🎓 Educational Choices Summary

All modeling decisions are based on:
1. **Statistical best practices**: Standard approaches in mixed-effects modeling
2. **Prosody research literature**: Established methods in speech prosody analysis
3. **Theoretical motivation**: Research questions drive model structure
4. **Practical considerations**: Balance between complexity and interpretability
5. **Empirical validation**: Pilot testing validates choices

**Key principle**: Start simple, add complexity only if justified by theory or data.

## 📝 CITI Training Note

As requested, please share CITI training information when available. This will be needed for:
- Human subjects research (if collecting naturalness ratings)
- Data sharing agreements
- IRB approval (if required)

## Conclusion

All requested components have been implemented and tested. The mixed-effects modeling framework is complete with configurable options, distribution checks, and interaction terms. Discourse markers and directionality interrelation analysis is implemented. Pilot tests have been run, revealing some convergence issues that need addressing. All design decisions are documented with clear reasoning.

The framework is ready for:
1. Full dataset analysis
2. Model refinement
3. Cross-corpus comparison
4. Naturalness investigation (scoping complete)
