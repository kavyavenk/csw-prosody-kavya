# Mixed-Effects Modeling: Design Decisions and Rationale

## Overview

This document outlines the educated choices made in designing the mixed-effects modeling framework for code-switched prosody analysis, with clear reasoning for each decision.

## 1. Random Effects Structure

### Decision: Hierarchical Random Effects (Speaker + Conversation)

**Structure**: `(1|speaker) + (1|conversation)`

**Rationale**:
- **Speaker-level variation**: Individual speakers have different baseline prosodic patterns (voice quality, speaking rate, etc.). This is well-established in prosody research.
- **Conversation-level variation**: Different conversations may have different topics, contexts, or interaction dynamics that affect prosody.
- **Nested structure**: Speakers are nested within conversations, but we use crossed random effects for simplicity and computational efficiency.

**Alternative considered**: Single random effect (speaker only)
- **Rejected because**: Conversations may introduce systematic variation (e.g., topic effects, turn-taking patterns) that should be accounted for.

**Toggle option**: Yes - users can disable random effects to compare with OLS models
- **Reason**: Allows comparison to assess whether random effects improve model fit

## 2. Fixed Effects Selection

### Decision: Condition + Functional Anchors + Directionality

**Base model**: `feature ~ condition + has_discourse_marker + has_repetition + is_l1_to_l2`

**Rationale**:
1. **Condition (CSW vs monolingual)**: Primary research question - do CSW utterances differ prosodically?
2. **Discourse markers**: Functional anchors hypothesis - do they modulate prosodic differences?
3. **Repetitions**: Another functional anchor - may indicate planning or disfluency
4. **Directionality (L1→L2 vs L2→L1)**: Tests whether switch direction matters

**Encoding choices**:
- **Condition**: Categorical (monolingual_EN, monolingual_L1, code_switched)
- **Discourse markers**: Binary (0/1) - simple and interpretable
- **Repetitions**: Binary (0/1) - captures presence/absence
- **Directionality**: Binary (0/1 for L1→L2, NaN for monolingual) - only applies to CSW

**Why binary for functional anchors?**
- Simpler than counts or continuous measures
- Focuses on presence/absence effect
- More interpretable coefficients
- Can be extended to counts if needed

## 3. Interaction Terms

### Decision: Include Key Interactions

**Interactions included**:
1. `condition × has_discourse_marker`: Tests if DM effect differs between CSW and monolingual
2. `has_discourse_marker × is_l1_to_l2`: Tests if DM effect differs by switch direction
3. `condition × is_l1_to_l2`: Tests if directionality effect differs between CSW and monolingual (redundant but included for completeness)

**Rationale**:
- **Condition × DM**: Addresses RQ3 - are prosodic differences modulated by functional anchors?
- **DM × Direction**: Tests interrelation hypothesis - do DMs appear more with certain directions and modulate prosody differently?
- **Condition × Direction**: Tests if directionality matters only in CSW context

**Why not all interactions?**
- Avoids overfitting with limited data
- Focuses on theoretically motivated interactions
- Can add more if initial models suggest they're needed

**Toggle option**: Yes - users can disable interactions
- **Reason**: Allows comparison to assess whether interactions improve model fit

## 4. Linear vs Nonlinear Modeling

### Decision: Start with Linear, Check Distributions

**Approach**:
1. Check feature distributions (skewness, kurtosis, normality tests)
2. Use linear models for approximately normal features
3. Consider transformations (log, sqrt) for moderately non-normal features
4. Consider nonlinear alternatives (GAM, splines) only if strongly non-normal

**Rationale**:
- **Linear models**: Simpler, more interpretable, standard in prosody research
- **Distribution checks**: Inform whether transformations are needed
- **Transformations**: Log-transform for right-skewed features (common in prosody)
- **Nonlinear models**: Only if linear fails and theory suggests nonlinearity

**Why not always nonlinear?**
- More complex, harder to interpret
- Requires more data
- May overfit
- Linear is standard in prosody research unless there's strong evidence for nonlinearity

**Implementation**: Distribution checks run automatically, recommendations provided

## 5. Feature Selection

### Decision: Prioritize Duration > Energy > Pitch

**Selection criteria**:
1. Duration features (highest priority - strongest effects in prior analysis)
2. Energy features (moderate priority)
3. Pitch features (lower priority - least affected in prior analysis)

**Within category**: Select by variance (proxy for informativeness)

**Rationale**:
- **Prior findings**: Duration features showed 96% significance, Energy 87.5%, Pitch ~30%
- **Variance**: Higher variance suggests more informative features
- **Balance**: Ensures representation across feature categories

**Alternative considered**: Select all features
- **Rejected because**: Too many features → multiple comparison problem, computational cost, overfitting risk

**Number of features**: Default 10, configurable
- **Reason**: Balance between comprehensiveness and computational efficiency

## 6. Model Fitting Methods

### Decision: Try Multiple Methods with Fallbacks

**Method sequence**:
1. Try `['lbfgs', 'powell']` (default)
2. Fallback to `'lbfgs'` only
3. Fallback to default method

**Rationale**:
- **LBFGS**: Fast, works well for most cases
- **Powell**: Alternative optimizer, sometimes works when LBFGS fails
- **Fallbacks**: Ensure models fit even if one method fails
- **Error handling**: Graceful degradation rather than failure

**Why not always use default?**
- Some models converge better with specific methods
- Multiple attempts increase success rate
- Non-fatal failures allow partial analysis

## 7. Model Comparison

### Decision: Use AIC and BIC

**Metrics**: AIC (Akaike Information Criterion) and BIC (Bayesian Information Criterion)

**Rationale**:
- **AIC**: Balances model fit and complexity, good for prediction
- **BIC**: Stronger penalty for complexity, good for model selection
- **Both**: Provide complementary information
- **Standard**: Widely used in mixed-effects modeling

**Alternative considered**: Only p-values
- **Rejected because**: P-values don't account for model complexity, can't compare non-nested models

**Report**: Both metrics included in output

## 8. Pilot Testing Strategy

### Decision: Test on Balanced Subsets First

**Pilot approach**:
- Use 500 utterances (250 CSW + 250 monolingual)
- Balanced by condition
- Test model structure before full analysis

**Rationale**:
- **Efficiency**: Faster iteration, catch issues early
- **Balance**: Ensures valid comparisons
- **Validation**: Test methodology before committing to full analysis
- **Debugging**: Easier to debug on smaller datasets

**Why 500?**
- Large enough for stable estimates
- Small enough for quick iteration
- ~10% of typical corpus size

**Full analysis**: Run after pilot validation
- **Reason**: Confirm findings on complete dataset

## 9. Handling Missing Data

### Decision: Listwise Deletion (Complete Cases)

**Approach**: Drop rows with any missing values in predictors or dependent variable

**Rationale**:
- **Simplicity**: Standard approach in mixed-effects modeling
- **Validity**: Ensures all models use same observations
- **Transparency**: Clear what data is used

**Alternative considered**: Multiple imputation
- **Not implemented because**: Adds complexity, may not be necessary if missingness is low
- **Future consideration**: If missingness is high, consider imputation

**Check**: Report number of observations after dropping NAs

## 10. Encoding Directionality

### Decision: Binary Indicator (L1→L2 = 1, L2→L1 = 0, NaN for monolingual)

**Encoding**:
- `is_l1_to_l2`: 1 if L1→L2, 0 if L2→L1, NaN if monolingual
- Only included in models for CSW utterances

**Rationale**:
- **Simple**: Binary is easier to interpret than categorical
- **Directional hypothesis**: Tests if L1→L2 differs from L2→L1
- **NaN for monolingual**: Correctly excludes from directionality analysis

**Alternative considered**: Categorical (L1→L2, L2→L1, None)
- **Rejected because**: Requires separate handling for monolingual, less interpretable coefficients

## 11. Statistical Significance

### Decision: Report p-values with Effect Sizes

**Reporting**:
- P-values for all fixed effects
- Effect sizes (coefficients) with confidence intervals
- Significance markers (*, **, ***)

**Rationale**:
- **P-values**: Standard statistical reporting
- **Effect sizes**: More informative than p-values alone
- **Confidence intervals**: Show uncertainty in estimates
- **Significance markers**: Quick visual reference

**Multiple comparisons**: Not corrected in initial models
- **Reason**: Exploratory analysis, can add FDR correction if needed
- **Future**: Consider FDR correction for multiple features

## Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Random effects | Speaker + Conversation | Account for hierarchical structure |
| Fixed effects | Condition + DM + Rep + Direction | Address all research questions |
| Interactions | Key interactions only | Balance theory and parsimony |
| Model type | Linear (with distribution checks) | Standard, interpretable |
| Feature selection | Duration > Energy > Pitch | Based on prior findings |
| Fitting method | Multiple with fallbacks | Maximize convergence |
| Comparison | AIC + BIC | Standard metrics |
| Pilot testing | Balanced 500-utterance subsets | Efficient validation |
| Missing data | Listwise deletion | Standard approach |
| Directionality | Binary indicator | Simple, interpretable |

## Future Considerations

1. **Nonlinear models**: If distribution checks suggest strong non-normality
2. **Multiple imputation**: If missingness is high
3. **FDR correction**: For multiple feature comparisons
4. **Random slopes**: If speaker effects vary by condition
5. **Bayesian models**: For small sample sizes or prior information

## References

- Bates et al. (2015) "Fitting Linear Mixed-Effects Models using lme4"
- Gelman & Hill (2006) "Data Analysis Using Regression and Multilevel/Hierarchical Models"
- Pinheiro & Bates (2000) "Mixed-Effects Models in S and S-PLUS"
