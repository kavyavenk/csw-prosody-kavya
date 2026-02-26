#!/usr/bin/env python3
"""
Analyze interrelation between discourse markers and code-switch directionality.

Research question: Are discourse markers more likely to appear with certain
switch directions? Do they modulate prosodic differences differently by direction?
"""

import argparse
import pathlib
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency
from typing import Dict

def analyze_dm_directionality_association(df: pd.DataFrame) -> Dict:
    """
    Analyze association between discourse markers and switch direction.
    
    Returns dict with:
    - contingency_table: Cross-tabulation
    - chi2_test: Chi-square test results
    - association_strength: Cramér's V
    """
    # Filter to CSW utterances only
    csw_df = df[df['lang'] == 'CS'].copy()
    
    if len(csw_df) == 0:
        return {'error': 'No CSW utterances found'}
    
    # Check if required columns exist
    has_dm_col = 'has_discourse_marker' in csw_df.columns
    has_dir_col = 'switch_direction_class' in csw_df.columns
    
    if not has_dm_col or not has_dir_col:
        return {'error': 'Missing required columns'}
    
    # Create binary indicators
    csw_df['has_dm'] = csw_df['has_discourse_marker'].astype(int)
    csw_df['has_direction'] = csw_df['switch_direction_class'].notna().astype(int)
    
    # Filter to utterances with direction info
    dir_df = csw_df[csw_df['has_direction'] == 1].copy()
    
    if len(dir_df) == 0:
        return {'error': 'No utterances with direction information'}
    
    # Create contingency table: DM × Direction
    dir_df['direction_binary'] = (dir_df['switch_direction_class'] == 'L1→L2').astype(int)
    dir_df['direction_label'] = dir_df['switch_direction_class'].map({
        'L1→L2': 'L1→L2',
        'L2→L1': 'L2→L1'
    })
    
    contingency = pd.crosstab(
        dir_df['has_dm'],
        dir_df['direction_label'],
        margins=True
    )
    
    # Chi-square test
    contingency_no_margins = pd.crosstab(
        dir_df['has_dm'],
        dir_df['direction_label']
    )
    
    chi2, p_value, dof, expected = chi2_contingency(contingency_no_margins)
    
    # Cramér's V (effect size)
    n = contingency_no_margins.sum().sum()
    min_dim = min(contingency_no_margins.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
    
    # Calculate proportions
    proportions = {}
    for direction in ['L1→L2', 'L2→L1']:
        if direction in dir_df['direction_label'].values:
            dir_subset = dir_df[dir_df['direction_label'] == direction]
            prop_with_dm = dir_subset['has_dm'].mean()
            proportions[direction] = {
                'pct_with_dm': prop_with_dm * 100,
                'n_total': len(dir_subset),
                'n_with_dm': dir_subset['has_dm'].sum()
            }
    
    return {
        'contingency_table': contingency,
        'chi2_statistic': chi2,
        'p_value': p_value,
        'degrees_of_freedom': dof,
        'cramers_v': cramers_v,
        'proportions': proportions,
        'n_total': len(dir_df)
    }

def analyze_prosodic_modulation_by_dm_direction(df: pd.DataFrame, feature: str) -> Dict:
    """
    Analyze how discourse markers modulate prosody differently by switch direction.
    
    Compares:
    1. L1→L2 with DM vs L1→L2 without DM
    2. L2→L1 with DM vs L2→L1 without DM
    3. Interaction effect
    """
    csw_df = df[df['lang'] == 'CS'].copy()
    
    if 'switch_direction_class' not in csw_df.columns or feature not in csw_df.columns:
        return {'error': 'Missing required columns'}
    
    # Filter to CSW with direction info
    dir_df = csw_df[csw_df['switch_direction_class'].notna()].copy()
    dir_df['has_dm'] = dir_df.get('has_discourse_marker', pd.Series([0] * len(dir_df))).astype(int)
    
    if len(dir_df) < 10:
        return {'error': 'Insufficient data'}
    
    results = {}
    
    # Compare by direction
    for direction in ['L1→L2', 'L2→L1']:
        dir_subset = dir_df[dir_df['switch_direction_class'] == direction]
        
        if len(dir_subset) < 5:
            continue
        
        with_dm = dir_subset[dir_subset['has_dm'] == 1][feature].dropna()
        without_dm = dir_subset[dir_subset['has_dm'] == 0][feature].dropna()
        
        if len(with_dm) > 2 and len(without_dm) > 2:
            tstat, pval = stats.ttest_ind(with_dm, without_dm)
            cohens_d = (with_dm.mean() - without_dm.mean()) / np.sqrt(
                (with_dm.var() + without_dm.var()) / 2
            ) if (with_dm.var() + without_dm.var()) > 0 else 0
            
            results[direction] = {
                'with_dm_mean': with_dm.mean(),
                'without_dm_mean': without_dm.mean(),
                'difference': with_dm.mean() - without_dm.mean(),
                't_statistic': tstat,
                'p_value': pval,
                'cohens_d': cohens_d,
                'n_with_dm': len(with_dm),
                'n_without_dm': len(without_dm)
            }
    
    # Test interaction: Is DM effect different between directions?
    if 'L1→L2' in results and 'L2→L1' in results:
        l1_l2_diff = results['L1→L2']['difference']
        l2_l1_diff = results['L2→L1']['difference']
        interaction_effect = l1_l2_diff - l2_l1_diff
        
        results['interaction'] = {
            'l1_l2_effect': l1_l2_diff,
            'l2_l1_effect': l2_l1_diff,
            'interaction_magnitude': interaction_effect,
            'interpretation': 'DM effect differs by direction' if abs(interaction_effect) > 0.1 else 'DM effect similar across directions'
        }
    
    return results

def run_interrelation_analysis(integrated_file: str, output_file: str, corpus: str):
    """
    Run complete interrelation analysis.
    """
    print(f"Loading integrated dataset from: {integrated_file}")
    df = pd.read_csv(integrated_file, low_memory=False)
    
    print(f"Total observations: {len(df)}")
    
    # Association analysis
    print("\n1. Analyzing association between discourse markers and direction...")
    association = analyze_dm_directionality_association(df)
    
    if 'error' not in association:
        print(f"  Chi-square test: χ²={association['chi2_statistic']:.3f}, "
              f"p={association['p_value']:.4f}")
        print(f"  Cramér's V: {association['cramers_v']:.3f}")
        print(f"\n  Proportions:")
        for direction, props in association['proportions'].items():
            print(f"    {direction}: {props['pct_with_dm']:.1f}% have DM "
                  f"({props['n_with_dm']}/{props['n_total']})")
    
    # Prosodic modulation analysis
    print("\n2. Analyzing prosodic modulation by DM × Direction...")
    prosodic_features = [c for c in df.columns if any(x in c.lower() 
                       for x in ['f0avg', 'f0std', 'f0max', 'f0min', 'duration', 'rate'])]
    
    if len(prosodic_features) > 10:
        prosodic_features = prosodic_features[:10]  # Limit for report
    
    modulation_results = {}
    for feature in prosodic_features:
        mod_result = analyze_prosodic_modulation_by_dm_direction(df, feature)
        if 'error' not in mod_result:
            modulation_results[feature] = mod_result
    
    # Generate report
    report_lines = []
    report_lines.append("# Discourse Markers × Switch Directionality Interrelation Analysis")
    report_lines.append(f"## Corpus: {corpus.upper()}\n")
    
    if 'error' not in association:
        report_lines.append("## Association Analysis\n")
        report_lines.append(f"**Chi-square test**: χ²={association['chi2_statistic']:.3f}, "
                          f"p={association['p_value']:.4f}, df={association['degrees_of_freedom']}")
        report_lines.append(f"**Cramér's V**: {association['cramers_v']:.3f}")
        report_lines.append("\n**Interpretation**:")
        if association['p_value'] < 0.05:
            report_lines.append("- Significant association between discourse markers and switch direction")
        else:
            report_lines.append("- No significant association")
        
        if association['cramers_v'] < 0.1:
            report_lines.append("- Weak association (Cramér's V < 0.1)")
        elif association['cramers_v'] < 0.3:
            report_lines.append("- Moderate association (0.1 < Cramér's V < 0.3)")
        else:
            report_lines.append("- Strong association (Cramér's V > 0.3)")
        
        report_lines.append("\n**Contingency Table**:")
        report_lines.append(association['contingency_table'].to_markdown())
    
    if modulation_results:
        report_lines.append("\n## Prosodic Modulation by DM × Direction\n")
        report_lines.append("| Feature | L1→L2: DM effect | L2→L1: DM effect | Interaction |")
        report_lines.append("|---------|------------------|------------------|-------------|")
        
        for feature, mod_result in list(modulation_results.items())[:10]:
            l1_l2 = mod_result.get('L1→L2', {})
            l2_l1 = mod_result.get('L2→L1', {})
            interaction = mod_result.get('interaction', {})
            
            l1_l2_effect = l1_l2.get('difference', np.nan)
            l1_l2_p = l1_l2.get('p_value', np.nan)
            l2_l1_effect = l2_l1.get('difference', np.nan)
            l2_l1_p = l2_l1.get('p_value', np.nan)
            interaction_mag = interaction.get('interaction_magnitude', np.nan)
            
            l1_l2_sig = "*" if l1_l2_p < 0.05 else ""
            l2_l1_sig = "*" if l2_l1_p < 0.05 else ""
            
            report_lines.append(
                f"| {feature} | {l1_l2_effect:.3f}{l1_l2_sig} | "
                f"{l2_l1_effect:.3f}{l2_l1_sig} | {interaction_mag:.3f} |"
            )
        
        report_lines.append("\n* p < 0.05")
    
    # Save report
    output_path = pathlib.Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_text = "\n".join(report_lines)
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(f"\nSaved interrelation analysis to: {output_file}")
    
    return association, modulation_results

if __name__ == '__main__':
    from typing import Dict
    
    p = argparse.ArgumentParser(description='Analyze DM × Directionality interrelation')
    p.add_argument('--integrated', type=str, required=True,
                   help='Integrated features CSV')
    p.add_argument('--output', type=str, required=True,
                   help='Output report file')
    p.add_argument('--corpus', type=str, choices=['seame', 'masac'],
                   required=True)
    
    args = p.parse_args()
    
    run_interrelation_analysis(args.integrated, args.output, args.corpus)
