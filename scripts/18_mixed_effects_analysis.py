#!/usr/bin/env python3
"""
Enhanced mixed-effects modeling for CSW prosody analysis.

This script builds mixed-effects models with:
- Condition (CSW vs monolingual) as fixed effect
- Discourse markers, repetitions, directionality as predictors
- Speaker and conversation as random effects
- Model comparison and reporting
"""

import argparse
import pathlib
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from scipy import stats
from typing import List
import warnings
warnings.filterwarnings('ignore')

# Manifest is source of truth for metadata; feature CSV may duplicate speaker/lang/condition.
_META_OVERLAP = ("speaker", "lang", "condition", "speaker_id", "speaker_raw", "text")


def formula_lhs(column_name: str) -> str:
    """Quote outcome name for patsy when not a valid identifier (e.g. 1F0max)."""
    if column_name.isidentifier():
        return column_name
    esc = str(column_name).replace("\\", "\\\\").replace('"', '\\"')
    return f'Q("{esc}")'


def merge_features_and_manifest(feature_df: pd.DataFrame, manifest_df: pd.DataFrame) -> pd.DataFrame:
    drop_cols = [c for c in _META_OVERLAP if c in feature_df.columns]
    feat_trim = feature_df.drop(columns=drop_cols, errors="ignore")
    return feat_trim.merge(manifest_df, on="utt_id", how="inner")


def choose_predictors(df: pd.DataFrame) -> List[str]:
    """Select available covariates while avoiding unstable high-cardinality factors."""
    predictors = ["condition"]
    optional_binary = ["has_discourse_marker", "has_repetition", "is_csw"]
    for col in optional_binary:
        if col in df.columns:
            predictors.append(col)

    categorical = [
        "gender",
        "age_bucket",
        "nationality",
        "dialogue_act",
        "audience_proficiency_proxy",
    ]
    for col in categorical:
        if col not in df.columns:
            continue
        non_null = df[col].dropna().astype(str)
        n_levels = non_null.nunique()
        if n_levels <= 1:
            continue
        if n_levels > 20:
            print(f"Skipping {col}: high cardinality ({n_levels} levels)")
            continue
        predictors.append(col)
    return predictors


def select_key_features(feature_df: pd.DataFrame, n_features: int = 10) -> List[str]:
    """
    Select key features for modeling based on variance and significance.
    
    Prioritizes:
    1. Duration features (highest significance in prior analysis)
    2. Energy features
    3. Pitch features
    """
    # Feature categories based on naming patterns
    duration_features = [col for col in feature_df.columns 
                        if any(x in col.lower() for x in ['duration', 'rate', 'pause', 'silence'])]
    energy_features = [col for col in feature_df.columns 
                      if any(x in col.lower() for x in ['energy', 'intensity', 'eavg', 'estd'])]
    pitch_features = [col for col in feature_df.columns 
                     if any(x in col.lower() for x in ['f0', 'pitch', 'f0avg', 'f0std', 'f0max', 'f0min'])]
    
    # Select top features by variance (proxy for informativeness)
    all_features = duration_features + energy_features + pitch_features
    available_features = [f for f in all_features if f in feature_df.columns]
    
    if len(available_features) == 0:
        # Fallback: use numeric columns
        numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
        # Exclude metadata columns
        exclude = ['speaker', 'n_switches', 'n_discourse_markers', 'n_repetitions']
        available_features = [c for c in numeric_cols if c not in exclude]
    
    # Sort by variance and take top N
    variances = feature_df[available_features].var().sort_values(ascending=False)
    selected = []
    seen = set()
    for fname in variances.index:
        if fname in seen:
            continue
        seen.add(fname)
        selected.append(fname)
        if len(selected) >= n_features:
            break
    return selected

def build_mixed_effects_model(feature_df: pd.DataFrame, feature: str, 
                              predictors: List[str], random_effects: List[str],
                              corpus: str) -> dict:
    """
    Build a mixed-effects model for a single feature.
    
    Args:
        feature_df: DataFrame with features and predictors
        feature: Name of dependent variable (prosodic feature)
        predictors: List of predictor names (fixed effects)
        random_effects: List of random effect grouping variables
        corpus: Corpus name
    
    Returns dict with model results and statistics.
    """
    # Prepare data
    model_df = feature_df[[feature] + predictors + random_effects].copy()
    model_df = model_df.dropna()
    
    if len(model_df) < 10:
        return {
            'success': False,
            'error': 'Insufficient data after removing NAs'
        }
    
    # Build formula
    # Fixed effects
    fixed_terms = [f'C({p})' if feature_df[p].dtype == 'object' else p for p in predictors]
    # Core interactions to test modulation of CS effects by speaker/interaction factors.
    interaction_terms = []
    interaction_bases = ["gender", "age_bucket", "nationality", "dialogue_act", "audience_proficiency_proxy"]
    for col in interaction_bases:
        if col in predictors and "condition" in predictors:
            interaction_terms.append(f"C(condition):C({col})")
    fixed_effects = " + ".join(fixed_terms + interaction_terms)
    formula = f"{formula_lhs(feature)} ~ {fixed_effects}"
    
    # Random effects: first grouping variable, or OLS if none
    groups = random_effects[0] if random_effects else None

    try:
        if groups:
            model = smf.mixedlm(formula, model_df, groups=model_df[groups])
            try:
                result = model.fit(method=['lbfgs', 'powell'])
            except Exception:
                try:
                    result = model.fit(method='lbfgs')
                except Exception:
                    result = model.fit()
        else:
            model = smf.ols(formula, model_df)
            result = model.fit()
        
        summary = result.summary()
        aic = getattr(result, "aic", np.nan)
        bic = getattr(result, "bic", np.nan)
        llf = getattr(result, "llf", np.nan)
        pvalues = result.pvalues
        n_groups = model_df[groups].nunique() if groups else None

        return {
            'success': True,
            'feature': feature,
            'formula': formula,
            'aic': aic,
            'bic': bic,
            'log_likelihood': llf,
            'pvalues': pvalues.to_dict(),
            'fixed_effects': result.params.to_dict(),
            'summary': str(summary),
            'n_observations': len(model_df),
            'n_groups': n_groups,
            'group_var': groups,
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def compare_models(model_results: List[dict]) -> pd.DataFrame:
    """
    Compare multiple models and create summary table.
    """
    rows = []
    for res in model_results:
        if res.get('success'):
            rows.append({
                'feature': res['feature'],
                'aic': res['aic'],
                'bic': res['bic'],
                'log_likelihood': res['log_likelihood'],
                'n_obs': res['n_observations'],
                'n_groups': res['n_groups']
            })
    
    if not rows:
        return pd.DataFrame()
    
    return pd.DataFrame(rows)

def run_mixed_effects_analysis(feature_file: str, manifest_file: str,
                              output_dir: str, corpus: str, 
                              n_features: int = 10):
    """
    Run mixed-effects analysis on prosodic features.
    """
    print(f"Loading features from: {feature_file}")
    feature_df = pd.read_csv(feature_file, low_memory=False)
    
    print(f"Loading manifest from: {manifest_file}")
    manifest_df = pd.read_csv(manifest_file, low_memory=False)
    
    # Merge features with manifest (manifest wins for speaker / condition / lang)
    print("\nMerging features with manifest...")
    df = merge_features_and_manifest(feature_df, manifest_df)
    
    print(f"Total observations: {len(df)}")
    
    # Select key features
    print(f"\nSelecting top {n_features} features for modeling...")
    key_features = select_key_features(df, n_features)
    print(f"Selected features: {', '.join(key_features[:5])}...")
    
    # Prepare predictors (speaker/interaction covariates included when available)
    predictors = choose_predictors(df)
    
    # Determine random effects (speaker-only random intercepts when IDs are usable)
    random_effects = []
    sp_col = "speaker_id" if "speaker_id" in df.columns else "speaker"
    if sp_col in df.columns:
        n_sp = df[sp_col].nunique()
        bad = df[sp_col].astype(str).str.lower().isin(["unknown", "nan", ""])
        if n_sp > 1 and bad.mean() < 0.95:
            random_effects.append(sp_col)
    print(f"\nPredictors: {', '.join(predictors)}")
    print(f"Random effects: {', '.join(random_effects) if random_effects else 'None (OLS)'}")
    
    # Build models for each feature
    print(f"\nBuilding models for {len(key_features)} features...")
    model_results = []
    
    for i, feature in enumerate(key_features):
        if i % 2 == 0:
            print(f"  Processing feature {i+1}/{len(key_features)}: {feature}")
        
        result = build_mixed_effects_model(
            df, feature, predictors, random_effects, corpus
        )
        result['feature'] = feature
        model_results.append(result)
    
    # Create summary
    print("\nCreating model comparison summary...")
    comparison_df = compare_models(model_results)
    
    # Save results
    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save model comparison
    comparison_file = output_path / f"{corpus}_mixed_effects_comparison.csv"
    comparison_df.to_csv(comparison_file, index=False)
    print(f"\nSaved model comparison to: {comparison_file}")
    
    # Save detailed results
    results_file = output_path / f"{corpus}_mixed_effects_results.txt"
    with open(results_file, 'w') as f:
        f.write(f"Mixed-Effects Modeling Results: {corpus.upper()}\n")
        f.write("=" * 80 + "\n\n")
        
        successful = [r for r in model_results if r.get('success')]
        failed = [r for r in model_results if not r.get('success')]
        
        f.write(f"Successful models: {len(successful)}/{len(model_results)}\n")
        f.write(f"Failed models: {len(failed)}\n\n")
        
        if failed:
            f.write("Failed Models:\n")
            for res in failed:
                f.write(f"  {res['feature']}: {res.get('error', 'Unknown error')}\n")
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("MODEL SUMMARIES\n")
        f.write("=" * 80 + "\n\n")
        
        for res in successful:
            f.write(f"\nFeature: {res['feature']}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Formula: {res['formula']}\n")
            aic_s = f"{res['aic']:.2f}" if res.get("aic") == res.get("aic") else "nan"
            bic_s = f"{res['bic']:.2f}" if res.get("bic") == res.get("bic") else "nan"
            f.write(f"AIC: {aic_s}, BIC: {bic_s}\n")
            f.write(f"N observations: {res['n_observations']}, N groups: {res['n_groups']}\n")
            f.write(f"\nFixed Effects:\n")
            for param, value in res['fixed_effects'].items():
                pval = res['pvalues'].get(param, np.nan)
                sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""
                f.write(f"  {param}: {value:.4f} (p={pval:.4f}){sig}\n")
            f.write("\n")
    
    print(f"Saved detailed results to: {results_file}")
    
    # Print summary statistics
    print("\n=== Model Summary ===")
    print(f"Successful models: {len(successful)}/{len(model_results)}")
    if len(successful) > 0:
        print(f"Mean AIC: {comparison_df['aic'].mean():.2f}")
        print(f"Mean BIC: {comparison_df['bic'].mean():.2f}")
    
    return model_results, comparison_df

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Run mixed-effects modeling on CSW prosody features'
    )
    p.add_argument('--features', type=str, required=True,
                   help='Input features CSV file')
    p.add_argument('--manifest', type=str, required=True,
                   help='Input manifest CSV file (with annotations)')
    p.add_argument('--output-dir', type=str, default='results/mixed_effects',
                   help='Output directory for results')
    p.add_argument('--corpus', type=str, choices=['seame', 'masac'],
                   required=True, help='Corpus name')
    p.add_argument('--n-features', type=int, default=10,
                   help='Number of features to model (default: 10)')
    
    args = p.parse_args()
    
    feature_file = pathlib.Path(args.features)
    manifest_file = pathlib.Path(args.manifest)
    
    if not feature_file.exists():
        print(f"ERROR: Feature file not found: {feature_file}")
        exit(1)
    
    if not manifest_file.exists():
        print(f"ERROR: Manifest file not found: {manifest_file}")
        exit(1)
    
    run_mixed_effects_analysis(
        str(feature_file), str(manifest_file), args.output_dir, 
        args.corpus, args.n_features
    )
