#!/usr/bin/env python3
"""
Generate report on discourse markers and repetitions as functional anchors.

This script analyzes how discourse markers and repetitions modulate prosodic
differences in code-switched speech.
"""

import argparse
import pathlib
import pandas as pd
import numpy as np
from scipy import stats

def compare_with_functional_anchors(df: pd.DataFrame, feature: str, 
                                   anchor_type: str = 'discourse_marker') -> dict:
    """
    Compare prosodic features between CSW and monolingual, stratified by functional anchors.
    
    Args:
        df: Integrated dataset
        feature: Prosodic feature name
        anchor_type: 'discourse_marker' or 'repetition'
    
    Returns dict with comparison statistics.
    """
    if anchor_type == 'discourse_marker':
        anchor_col = 'has_dm'
        anchor_name = 'discourse marker'
    elif anchor_type == 'repetition':
        anchor_col = 'has_rep'
        anchor_name = 'repetition'
    else:
        raise ValueError(f"Unknown anchor type: {anchor_type}")
    
    if anchor_col not in df.columns:
        return {'error': f'Column {anchor_col} not found'}
    
    if feature not in df.columns:
        return {'error': f'Feature {feature} not found'}
    
    # Filter valid data
    valid_df = df[[feature, 'is_csw', anchor_col]].dropna()
    
    if len(valid_df) < 10:
        return {'error': 'Insufficient data'}
    
    results = {}
    
    # Comparison 1: CSW vs Monolingual, WITH anchor
    with_anchor = valid_df[valid_df[anchor_col] == 1]
    if len(with_anchor) > 5:
        csw_with = with_anchor[with_anchor['is_csw'] == 1][feature]
        mono_with = with_anchor[with_anchor['is_csw'] == 0][feature]
        
        if len(csw_with) > 2 and len(mono_with) > 2:
            tstat, pval = stats.ttest_ind(csw_with, mono_with)
            cohens_d = (csw_with.mean() - mono_with.mean()) / np.sqrt(
                (csw_with.var() + mono_with.var()) / 2
            )
            
            results['with_anchor'] = {
                'csw_mean': csw_with.mean(),
                'mono_mean': mono_with.mean(),
                'difference': csw_with.mean() - mono_with.mean(),
                't_statistic': tstat,
                'p_value': pval,
                'cohens_d': cohens_d,
                'n_csw': len(csw_with),
                'n_mono': len(mono_with)
            }
    
    # Comparison 2: CSW vs Monolingual, WITHOUT anchor
    without_anchor = valid_df[valid_df[anchor_col] == 0]
    if len(without_anchor) > 5:
        csw_without = without_anchor[without_anchor['is_csw'] == 1][feature]
        mono_without = without_anchor[without_anchor['is_csw'] == 0][feature]
        
        if len(csw_without) > 2 and len(mono_without) > 2:
            tstat, pval = stats.ttest_ind(csw_without, mono_without)
            cohens_d = (csw_without.mean() - mono_without.mean()) / np.sqrt(
                (csw_without.var() + mono_without.var()) / 2
            )
            
            results['without_anchor'] = {
                'csw_mean': csw_without.mean(),
                'mono_mean': mono_without.mean(),
                'difference': csw_without.mean() - mono_without.mean(),
                't_statistic': tstat,
                'p_value': pval,
                'cohens_d': cohens_d,
                'n_csw': len(csw_without),
                'n_mono': len(mono_without)
            }
    
    # Comparison 3: CSW with anchor vs CSW without anchor
    csw_df = valid_df[valid_df['is_csw'] == 1]
    if len(csw_df) > 5:
        csw_with_anchor = csw_df[csw_df[anchor_col] == 1][feature]
        csw_without_anchor = csw_df[csw_df[anchor_col] == 0][feature]
        
        if len(csw_with_anchor) > 2 and len(csw_without_anchor) > 2:
            tstat, pval = stats.ttest_ind(csw_with_anchor, csw_without_anchor)
            cohens_d = (csw_with_anchor.mean() - csw_without_anchor.mean()) / np.sqrt(
                (csw_with_anchor.var() + csw_without_anchor.var()) / 2
            )
            
            results['csw_anchor_effect'] = {
                'with_anchor_mean': csw_with_anchor.mean(),
                'without_anchor_mean': csw_without_anchor.mean(),
                'difference': csw_with_anchor.mean() - csw_without_anchor.mean(),
                't_statistic': tstat,
                'p_value': pval,
                'cohens_d': cohens_d,
                'n_with': len(csw_with_anchor),
                'n_without': len(csw_without_anchor)
            }
    
    return results

def generate_report(integrated_file: str, output_file: str, corpus: str):
    """
    Generate comprehensive report on functional anchors analysis.
    """
    print(f"Loading integrated dataset from: {integrated_file}")
    df = pd.read_csv(integrated_file, low_memory=False)
    
    print(f"Total observations: {len(df)}")
    
    # Select key features
    prosodic_features = [c for c in df.columns if any(x in c.lower() 
                       for x in ['f0avg', 'f0std', 'f0max', 'f0min', 'duration', 
                                'rate', 'pause', 'energy', 'intensity'])]
    
    # Limit to top features by variance
    if len(prosodic_features) > 20:
        variances = df[prosodic_features].var().sort_values(ascending=False)
        prosodic_features = variances.head(20).index.tolist()
    
    print(f"\nAnalyzing {len(prosodic_features)} prosodic features...")
    
    # Analyze discourse markers
    print("\nAnalyzing discourse markers as functional anchors...")
    dm_results = {}
    
    for feature in prosodic_features[:10]:  # Limit for report
        result = compare_with_functional_anchors(df, feature, 'discourse_marker')
        if 'error' not in result:
            dm_results[feature] = result
    
    # Analyze repetitions
    print("Analyzing repetitions as functional anchors...")
    rep_results = {}
    
    for feature in prosodic_features[:10]:
        result = compare_with_functional_anchors(df, feature, 'repetition')
        if 'error' not in result:
            rep_results[feature] = result
    
    # Generate report
    report_lines = []
    report_lines.append("# Functional Anchors Analysis Report")
    report_lines.append(f"## Corpus: {corpus.upper()}")
    report_lines.append("")
    report_lines.append(f"Generated from integrated dataset: {integrated_file}")
    report_lines.append(f"Total observations: {len(df)}")
    report_lines.append("")
    
    # Discourse markers section
    report_lines.append("## Discourse Markers as Functional Anchors")
    report_lines.append("")
    
    if dm_results:
        report_lines.append("### Summary Statistics")
        report_lines.append("")
        report_lines.append("| Feature | CSW vs Mono (with DM) | CSW vs Mono (without DM) | CSW: DM effect |")
        report_lines.append("|---------|----------------------|-------------------------|----------------|")
        
        for feature, result in list(dm_results.items())[:10]:
            with_anchor = result.get('with_anchor', {})
            without_anchor = result.get('without_anchor', {})
            anchor_effect = result.get('csw_anchor_effect', {})
            
            with_diff = with_anchor.get('difference', np.nan)
            with_p = with_anchor.get('p_value', np.nan)
            without_diff = without_anchor.get('difference', np.nan)
            without_p = without_anchor.get('p_value', np.nan)
            effect_diff = anchor_effect.get('difference', np.nan)
            effect_p = anchor_effect.get('p_value', np.nan)
            
            with_sig = "*" if with_p < 0.05 else ""
            without_sig = "*" if without_p < 0.05 else ""
            effect_sig = "*" if effect_p < 0.05 else ""
            
            report_lines.append(
                f"| {feature} | {with_diff:.3f}{with_sig} | {without_diff:.3f}{without_sig} | "
                f"{effect_diff:.3f}{effect_sig} |"
            )
        
        report_lines.append("")
        report_lines.append("* p < 0.05")
        report_lines.append("")
    
    # Repetitions section
    report_lines.append("## Repetitions as Functional Anchors")
    report_lines.append("")
    
    if rep_results:
        report_lines.append("### Summary Statistics")
        report_lines.append("")
        report_lines.append("| Feature | CSW vs Mono (with Rep) | CSW vs Mono (without Rep) | CSW: Rep effect |")
        report_lines.append("|---------|----------------------|-------------------------|----------------|")
        
        for feature, result in list(rep_results.items())[:10]:
            with_anchor = result.get('with_anchor', {})
            without_anchor = result.get('without_anchor', {})
            anchor_effect = result.get('csw_anchor_effect', {})
            
            with_diff = with_anchor.get('difference', np.nan)
            with_p = with_anchor.get('p_value', np.nan)
            without_diff = without_anchor.get('difference', np.nan)
            without_p = without_anchor.get('p_value', np.nan)
            effect_diff = anchor_effect.get('difference', np.nan)
            effect_p = anchor_effect.get('p_value', np.nan)
            
            with_sig = "*" if with_p < 0.05 else ""
            without_sig = "*" if without_p < 0.05 else ""
            effect_sig = "*" if effect_p < 0.05 else ""
            
            report_lines.append(
                f"| {feature} | {with_diff:.3f}{with_sig} | {without_diff:.3f}{without_sig} | "
                f"{effect_diff:.3f}{effect_sig} |"
            )
        
        report_lines.append("")
        report_lines.append("* p < 0.05")
        report_lines.append("")
    
    # Key findings
    report_lines.append("## Key Findings")
    report_lines.append("")
    
    # Count significant effects
    dm_significant = sum(1 for r in dm_results.values() 
                        if r.get('csw_anchor_effect', {}).get('p_value', 1) < 0.05)
    rep_significant = sum(1 for r in rep_results.values() 
                         if r.get('csw_anchor_effect', {}).get('p_value', 1) < 0.05)
    
    report_lines.append(f"- Discourse markers modulate prosodic differences in "
                       f"{dm_significant}/{len(dm_results)} features analyzed")
    report_lines.append(f"- Repetitions modulate prosodic differences in "
                       f"{rep_significant}/{len(rep_results)} features analyzed")
    report_lines.append("")
    
    # Save report
    output_path = pathlib.Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_text = "\n".join(report_lines)
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(f"\nSaved report to: {output_file}")
    
    return report_lines

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Generate functional anchors analysis report'
    )
    p.add_argument('--integrated', type=str, required=True,
                   help='Input integrated dataset CSV')
    p.add_argument('--output', type=str, required=True,
                   help='Output report markdown file')
    p.add_argument('--corpus', type=str, choices=['seame', 'masac'],
                   required=True, help='Corpus name')
    
    args = p.parse_args()
    
    integrated_file = pathlib.Path(args.integrated)
    if not integrated_file.exists():
        print(f"ERROR: Integrated file not found: {integrated_file}")
        exit(1)
    
    generate_report(str(integrated_file), args.output, args.corpus)
