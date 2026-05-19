#!/usr/bin/env python3
"""
Enhanced Mixed-Effects Modeling with configurable options.

Features:
- Toggle for random effects (speaker, conversation, both, or none)
- Distribution checks for linear vs nonlinear modeling
- Interaction terms (discourse markers × directionality)
- Model comparison and selection
- Pilot testing on subsets
"""

import argparse
import pathlib
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from scipy import stats
from typing import List, Optional, Dict
import warnings
warnings.filterwarnings('ignore')

_META_OVERLAP = ("speaker", "lang", "condition", "speaker_id", "speaker_raw", "text")


def merge_features_and_manifest(feature_df: pd.DataFrame, manifest_df: pd.DataFrame) -> pd.DataFrame:
    drop_cols = [c for c in _META_OVERLAP if c in feature_df.columns]
    feat_trim = feature_df.drop(columns=drop_cols, errors="ignore")
    return feat_trim.merge(manifest_df, on="utt_id", how="inner")


def check_feature_distribution(feature_values: pd.Series) -> Dict[str, any]:
    """
    Check feature distribution to inform linear vs nonlinear modeling choice.
    
    Returns dict with:
    - is_normal: Shapiro-Wilk test result (if n < 5000)
    - skewness: measure of asymmetry
    - kurtosis: measure of tail heaviness
    - recommendation: 'linear' or 'nonlinear'
    """
    values = feature_values.dropna()
    if len(values) < 3:
        return {'recommendation': 'linear', 'reason': 'insufficient_data'}
    
    # Calculate skewness and kurtosis
    skew = stats.skew(values)
    kurt = stats.kurtosis(values)
    
    # Shapiro-Wilk test for normality (only if sample size allows)
    is_normal = None
    if len(values) < 5000:
        try:
            _, p_norm = stats.shapiro(values[:min(5000, len(values))])
            is_normal = p_norm > 0.05
        except:
            pass
    
    # Recommendation logic
    # Strongly non-normal: |skew| > 2 or |kurt| > 5 → consider nonlinear
    # Moderately non-normal: |skew| > 1 or |kurt| > 3 → linear OK but log-transform might help
    # Normal: linear is fine
    if abs(skew) > 2 or abs(kurt) > 5:
        recommendation = 'nonlinear'
        reason = f'strong_non_normal (skew={skew:.2f}, kurt={kurt:.2f})'
    elif abs(skew) > 1 or abs(kurt) > 3:
        recommendation = 'linear_with_transform'
        reason = f'moderate_non_normal (skew={skew:.2f}, kurt={kurt:.2f})'
    else:
        recommendation = 'linear'
        reason = f'approximately_normal (skew={skew:.2f}, kurt={kurt:.2f})'
    
    return {
        'is_normal': is_normal,
        'skewness': skew,
        'kurtosis': kurt,
        'recommendation': recommendation,
        'reason': reason
    }

def build_linear_mixed_model(feature_df: pd.DataFrame, feature: str,
                            predictors: List[str], random_effects: List[str],
                            use_interactions: bool = True) -> Dict:
    """
    Build linear mixed-effects model.
    
    Args:
        feature_df: DataFrame with features and predictors
        feature: Dependent variable name
        predictors: List of predictor names
        random_effects: List of random effect grouping variables
        use_interactions: Whether to include interaction terms
    
    Returns dict with model results.
    """
    # Prepare data
    model_df = feature_df[[feature] + predictors + random_effects].copy()
    model_df = model_df.dropna()
    
    if len(model_df) < 10:
        return {'success': False, 'error': 'Insufficient data'}
    
    # Build formula
    # Base fixed effects
    fixed_effects = []
    for p in predictors:
        if feature_df[p].dtype == 'object' or feature_df[p].dtype.name == 'category':
            fixed_effects.append(f'C({p})')
        else:
            fixed_effects.append(p)
    
    # Add interactions if requested
    if use_interactions and len(predictors) >= 2:
        # Interaction: discourse_marker × directionality (if both present)
        if 'has_discourse_marker' in predictors and 'is_l1_to_l2' in predictors:
            fixed_effects.append('has_discourse_marker:is_l1_to_l2')
        # Interaction: condition × discourse_marker
        if 'condition' in predictors and 'has_discourse_marker' in predictors:
            fixed_effects.append('condition:has_discourse_marker')
        # Interaction: condition × directionality (for CSW only)
        if 'condition' in predictors and 'is_l1_to_l2' in predictors:
            fixed_effects.append('condition:is_l1_to_l2')
        for col in ["gender", "age_bucket", "nationality", "dialogue_act", "audience_proficiency_proxy"]:
            if "condition" in predictors and col in predictors:
                fixed_effects.append(f"C(condition):C({col})")
    
    formula = f"{feature} ~ {' + '.join(fixed_effects)}"
    
    # Random effects structure
    groups = random_effects[0] if random_effects else None
    
    try:
        if groups:
            model = smf.mixedlm(formula, model_df, groups=model_df[groups])
        else:
            # No random effects - use OLS
            model = smf.ols(formula, model_df)
        
        # Fit model
        try:
            if groups:
                result = model.fit(method=['lbfgs', 'powell'])
            else:
                result = model.fit()
        except:
            if groups:
                result = model.fit(method='lbfgs')
            else:
                result = model.fit()
        
        return {
            'success': True,
            'feature': feature,
            'formula': formula,
            'model_type': 'mixed' if groups else 'ols',
            'aic': result.aic,
            'bic': result.bic,
            'log_likelihood': result.llf if hasattr(result, 'llf') else None,
            'pvalues': result.pvalues.to_dict(),
            'fixed_effects': result.params.to_dict(),
            'n_observations': len(model_df),
            'n_groups': model_df[groups].nunique() if groups else None,
            'summary': str(result.summary())
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def build_model_with_options(feature_df: pd.DataFrame, feature: str,
                             predictors: List[str], random_effects: List[str],
                             use_random_effects: bool = True,
                             use_interactions: bool = True) -> Dict:
    """
    Build model with configurable options.
    """
    # Select random effects based on toggle
    active_random_effects = random_effects if use_random_effects else []
    
    return build_linear_mixed_model(
        feature_df, feature, predictors, active_random_effects, use_interactions
    )

def run_pilot_analysis(feature_file: str, manifest_file: str,
                      output_dir: str, corpus: str,
                      n_features: int = 5, subset_size: int = 500,
                      use_random_effects: bool = True,
                      use_interactions: bool = True):
    """
    Run pilot analysis on a subset of data.
    
    Args:
        subset_size: Number of utterances to use for pilot (default: 500)
    """
    print(f"PILOT ANALYSIS: Using subset of {subset_size} utterances")
    print(f"Loading features from: {feature_file}")
    feature_df = pd.read_csv(feature_file, low_memory=False)
    
    print(f"Loading manifest from: {manifest_file}")
    manifest_df = pd.read_csv(manifest_file, low_memory=False)
    
    df = merge_features_and_manifest(feature_df, manifest_df)
    
    # Create balanced subset
    print(f"\nCreating balanced subset (n={subset_size})...")
    cs_df = df[df['lang'] == 'CS'].copy()
    mono_df = df[df['lang'] != 'CS'].copy()
    
    n_per_group = subset_size // 2
    cs_sample = cs_df.sample(n=min(n_per_group, len(cs_df)), random_state=42)
    mono_sample = mono_df.sample(n=min(n_per_group, len(mono_df)), random_state=42)
    
    pilot_df = pd.concat([cs_sample, mono_sample]).reset_index(drop=True)
    print(f"  CSW: {len(cs_sample)}, Monolingual: {len(mono_sample)}")
    
    # Select features
    print(f"\nSelecting {n_features} features for pilot...")
    key_features = select_key_features(pilot_df, n_features)
    print(f"Selected: {', '.join(key_features)}")
    
    # Check distributions
    print("\nChecking feature distributions...")
    dist_info = {}
    for feat in key_features:
        info = check_feature_distribution(pilot_df[feat])
        dist_info[feat] = info
        print(f"  {feat}: {info['recommendation']} ({info['reason']})")

    # Apply simple log-style transforms where recommended to stabilize distributions.
    # We keep the original feature columns and add new log_*-style columns as needed.
    transformed_features = []
    for feat in key_features:
        info = dist_info[feat]
        rec = info.get("recommendation")
        if rec in ("linear_with_transform", "nonlinear"):
            series = pilot_df[feat]
            min_val = series.min()
            if pd.isna(min_val):
                shifted = series.fillna(0) + 1e-3
            elif min_val <= 0:
                shift = (0 - min_val) + 1e-3
                shifted = series + shift
            else:
                shifted = series
            new_name = f"log_{feat}"
            pilot_df[new_name] = np.log1p(shifted)
            transformed_features.append(new_name)
        else:
            transformed_features.append(feat)

    modeling_features = transformed_features
    
    # Prepare predictors
    predictors = ['condition']
    if 'has_discourse_marker' in pilot_df.columns:
        predictors.append('has_discourse_marker')
    if 'has_repetition' in pilot_df.columns:
        predictors.append('has_repetition')
    for col in ["gender", "age_bucket", "nationality", "dialogue_act", "audience_proficiency_proxy"]:
        if col in pilot_df.columns:
            n_levels = pilot_df[col].dropna().astype(str).nunique()
            if 1 < n_levels <= 20:
                predictors.append(col)
    # Do not add is_l1_to_l2 here: it is NaN for monolingual rows and makes dropna()
    # remove all mono utterances (same singular-matrix issue as script 18). Use
    # scripts/25_run_directionality_models.py for CS-only directionality.
    
    random_effects = []
    if use_random_effects:
        sp_col = "speaker_id" if "speaker_id" in pilot_df.columns else "speaker"
        if sp_col in pilot_df.columns:
            bad = pilot_df[sp_col].astype(str).str.lower().isin(["unknown", "nan", ""])
            if pilot_df[sp_col].nunique() > 1 and bad.mean() < 0.95:
                random_effects.append(sp_col)
    
    print(f"\nPredictors: {', '.join(predictors)}")
    print(f"Random effects: {', '.join(random_effects) if random_effects else 'None'}")
    print(f"Interactions: {'Yes' if use_interactions else 'No'}")
    
    # Build models
    print(f"\nBuilding models...")
    model_results = []
    
    for raw_feat, model_feat in zip(key_features, modeling_features):
        print(f"  {model_feat} (from {raw_feat})...", end=' ')
        result = build_model_with_options(
            pilot_df, model_feat, predictors, random_effects,
            use_random_effects, use_interactions
        )
        result['feature'] = model_feat
        result['original_feature'] = raw_feat
        result['distribution'] = dist_info[raw_feat]
        model_results.append(result)
        
        if result.get('success'):
            print(f"✓ (AIC={result['aic']:.1f})")
        else:
            print(f"✗ ({result.get('error', 'Unknown')[:30]})")
    
    # Save results
    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save summary
    summary_file = output_path / f"{corpus}_pilot_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Pilot Analysis Summary: {corpus.upper()}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Subset size: {subset_size}\n")
        f.write(f"Features tested: {len(key_features)}\n")
        f.write(f"Random effects: {', '.join(random_effects) if random_effects else 'None'}\n")
        f.write(f"Interactions: {'Yes' if use_interactions else 'No'}\n\n")
        
        successful = [r for r in model_results if r.get('success')]
        f.write(f"Successful models: {len(successful)}/{len(model_results)}\n\n")
        
        f.write("Feature Distribution Analysis:\n")
        for feat, info in dist_info.items():
            f.write(f"  {feat}:\n")
            f.write(f"    Recommendation: {info['recommendation']}\n")
            f.write(f"    Reason: {info['reason']}\n")
            f.write(f"    Skewness: {info['skewness']:.3f}, Kurtosis: {info['kurtosis']:.3f}\n\n")
        
        f.write("\nModel Results:\n")
        for res in model_results:
            f.write(f"\n{res['feature']}:\n")
            if res.get('success'):
                f.write(f"  AIC: {res['aic']:.2f}, BIC: {res['bic']:.2f}\n")
                f.write(f"  Formula: {res['formula']}\n")
            else:
                f.write(f"  Error: {res.get('error', 'Unknown')}\n")
    
    print(f"\nSaved pilot summary to: {summary_file}")
    
    return model_results, dist_info

def select_key_features(feature_df: pd.DataFrame, n_features: int = 10) -> List[str]:
    """Select key features for modeling."""
    duration_features = [col for col in feature_df.columns 
                        if any(x in col.lower() for x in ['duration', 'rate', 'pause', 'silence'])]
    energy_features = [col for col in feature_df.columns 
                      if any(x in col.lower() for x in ['energy', 'intensity', 'eavg', 'estd'])]
    pitch_features = [col for col in feature_df.columns 
                     if any(x in col.lower() for x in ['f0', 'pitch', 'f0avg', 'f0std', 'f0max', 'f0min'])]
    
    all_features = duration_features + energy_features + pitch_features
    available_features = [f for f in all_features if f in feature_df.columns]
    
    if len(available_features) == 0:
        numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
        exclude = ['speaker', 'n_switches', 'n_discourse_markers', 'n_repetitions']
        available_features = [c for c in numeric_cols if c not in exclude]
    
    variances = feature_df[available_features].var().sort_values(ascending=False)
    return variances.head(n_features).index.tolist()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Enhanced mixed-effects modeling with options')
    p.add_argument('--features', type=str, required=True, help='Features CSV')
    p.add_argument('--manifest', type=str, required=True, help='Manifest CSV')
    p.add_argument('--output-dir', type=str, default='results/mixed_effects',
                   help='Output directory')
    p.add_argument('--corpus', type=str, choices=['seame', 'masac'], required=True)
    p.add_argument('--n-features', type=int, default=5, help='Number of features')
    p.add_argument('--subset-size', type=int, default=500, help='Pilot subset size')
    p.add_argument('--no-random-effects', action='store_true',
                   help='Disable random effects')
    p.add_argument('--no-interactions', action='store_true',
                   help='Disable interaction terms')
    p.add_argument('--full', action='store_true',
                   help='Run on full dataset (not pilot)')
    
    args = p.parse_args()
    
    subset_size = None if args.full else args.subset_size
    use_random_effects = not args.no_random_effects
    use_interactions = not args.no_interactions
    
    if subset_size:
        run_pilot_analysis(
            args.features, args.manifest, args.output_dir, args.corpus,
            args.n_features, subset_size, use_random_effects, use_interactions
        )
    else:
        # Full analysis - would call existing script here
        print("Full analysis mode - use scripts/18_mixed_effects_analysis.py")
        print("This pilot script focuses on subset validation.")
