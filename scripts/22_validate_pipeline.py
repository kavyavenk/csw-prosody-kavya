#!/usr/bin/env python3
"""
Validate the complete analysis pipeline for missing components and errors.

This script checks:
1. All required input files exist
2. All scripts are present and executable
3. Output files are generated correctly
4. Data integrity checks
"""

import argparse
import pathlib
import pandas as pd
import sys

def check_file_exists(file_path: pathlib.Path, description: str) -> tuple:
    """Check if a file exists and return (exists, message)."""
    if file_path.exists():
        return (True, f"✓ {description}: {file_path}")
    else:
        return (False, f"✗ {description}: {file_path} (MISSING)")

def check_script_exists(script_name: str) -> tuple:
    """Check if a script exists and is executable."""
    script_path = pathlib.Path(__file__).parent / script_name
    if not script_path.exists():
        return (False, f"✗ Script missing: {script_name}")
    if not script_path.stat().st_mode & 0o111:
        return (False, f"✗ Script not executable: {script_name}")
    return (True, f"✓ Script exists: {script_name}")

def validate_corpus(corpus: str) -> dict:
    """Validate a corpus's pipeline."""
    results = {
        'corpus': corpus,
        'errors': [],
        'warnings': [],
        'checks_passed': []
    }
    
    print(f"\n{'='*80}")
    print(f"Validating {corpus.upper()} corpus pipeline")
    print(f"{'='*80}\n")
    
    # Check input files
    print("1. Checking input files...")
    manifest_file = pathlib.Path(f"manifests/{corpus}_manifest.csv")
    feature_file = pathlib.Path(f"features/{corpus}_disvoice_utt.csv")
    
    exists, msg = check_file_exists(manifest_file, f"{corpus} manifest")
    if exists:
        results['checks_passed'].append(msg)
        # Check manifest structure
        try:
            df = pd.read_csv(manifest_file, nrows=5)
            required_cols = ['utt_id', 'lang', 'condition', 'text']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                results['errors'].append(f"Manifest missing columns: {missing}")
            else:
                results['checks_passed'].append(f"Manifest has required columns")
        except Exception as e:
            results['errors'].append(f"Could not read manifest: {e}")
    else:
        results['errors'].append(msg)
    
    exists, msg = check_file_exists(feature_file, f"{corpus} features")
    if exists:
        results['checks_passed'].append(msg)
        # Check feature file structure
        try:
            df = pd.read_csv(feature_file, nrows=5)
            if 'utt_id' not in df.columns:
                results['errors'].append("Feature file missing 'utt_id' column")
            elif len(df.columns) < 10:
                results['warnings'].append(f"Feature file has only {len(df.columns)} columns (expected ~103)")
            else:
                results['checks_passed'].append(f"Feature file has {len(df.columns)} columns")
        except Exception as e:
            results['errors'].append(f"Could not read feature file: {e}")
    else:
        results['errors'].append(msg)
    
    # Check scripts
    print("\n2. Checking analysis scripts...")
    scripts = [
        '16_detect_discourse_markers_repetitions.py',
        '17_extract_switch_directionality.py',
        '18_mixed_effects_analysis.py',
        '19_integrate_features_for_analysis.py',
        '20_generate_functional_anchors_report.py',
        '21_run_functional_anchors_pipeline.py'
    ]
    
    for script in scripts:
        exists, msg = check_script_exists(script)
        if exists:
            results['checks_passed'].append(msg)
        else:
            results['errors'].append(msg)
    
    # Check output files
    print("\n3. Checking output files...")
    output_dir = pathlib.Path(f"results/functional_anchors/{corpus}")
    
    if output_dir.exists():
        results['checks_passed'].append(f"Output directory exists: {output_dir}")
        
        expected_files = [
            f"{corpus}_manifest_with_anchors.csv",
            f"{corpus}_manifest_with_direction.csv",
            f"{corpus}_integrated_features.csv",
            f"{corpus}_functional_anchors_report.md"
        ]
        
        for filename in expected_files:
            file_path = output_dir / filename
            exists, msg = check_file_exists(file_path, filename)
            if exists:
                results['checks_passed'].append(msg)
                # Validate file contents
                if filename.endswith('.csv'):
                    try:
                        df = pd.read_csv(file_path, nrows=5)
                        if len(df) == 0:
                            results['warnings'].append(f"{filename} is empty")
                        else:
                            results['checks_passed'].append(f"{filename} has data ({len(df)} rows)")
                    except Exception as e:
                        results['warnings'].append(f"Could not read {filename}: {e}")
            else:
                results['warnings'].append(msg)
    else:
        results['warnings'].append(f"Output directory does not exist: {output_dir}")
    
    # Check data integrity
    print("\n4. Checking data integrity...")
    if manifest_file.exists() and feature_file.exists():
        try:
            manifest_df = pd.read_csv(manifest_file)
            feature_df = pd.read_csv(feature_file)
            
            # Check utt_id overlap
            manifest_ids = set(manifest_df['utt_id'].unique())
            feature_ids = set(feature_df['utt_id'].unique())
            overlap = len(manifest_ids & feature_ids)
            
            if overlap > 0:
                results['checks_passed'].append(f"utt_id overlap: {overlap} utterances")
                overlap_pct = 100 * overlap / len(manifest_ids)
                if overlap_pct < 50:
                    results['warnings'].append(f"Low overlap: only {overlap_pct:.1f}% of manifest has features")
            else:
                results['errors'].append("No utt_id overlap between manifest and features")
            
            # Check language distribution
            if 'lang' in manifest_df.columns:
                lang_counts = manifest_df['lang'].value_counts()
                cs_count = lang_counts.get('CS', 0)
                total = len(manifest_df)
                if cs_count > 0:
                    cs_pct = 100 * cs_count / total
                    results['checks_passed'].append(f"CSW utterances: {cs_count} ({cs_pct:.1f}%)")
                    if cs_pct < 10:
                        results['warnings'].append(f"Low CSW percentage: {cs_pct:.1f}%")
                else:
                    results['errors'].append("No CSW utterances found in manifest")
            
        except Exception as e:
            results['errors'].append(f"Data integrity check failed: {e}")
    
    return results

def print_summary(results: dict):
    """Print validation summary."""
    print(f"\n{'='*80}")
    print(f"Validation Summary: {results['corpus'].upper()}")
    print(f"{'='*80}\n")
    
    print(f"✓ Checks passed: {len(results['checks_passed'])}")
    if results['checks_passed']:
        for check in results['checks_passed'][:10]:  # Show first 10
            print(f"  {check}")
        if len(results['checks_passed']) > 10:
            print(f"  ... and {len(results['checks_passed']) - 10} more")
    
    if results['warnings']:
        print(f"\n⚠ Warnings: {len(results['warnings'])}")
        for warning in results['warnings']:
            print(f"  {warning}")
    
    if results['errors']:
        print(f"\n✗ Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  {error}")
        return False
    else:
        print(f"\n✓ No errors found!")
        return True

def main():
    p = argparse.ArgumentParser(description='Validate analysis pipeline')
    p.add_argument('--corpus', type=str, choices=['seame', 'masac', 'both'],
                   default='both', help='Corpus to validate')
    
    args = p.parse_args()
    
    corpora = ['seame', 'masac'] if args.corpus == 'both' else [args.corpus]
    
    all_passed = True
    for corpus in corpora:
        results = validate_corpus(corpus)
        passed = print_summary(results)
        all_passed = all_passed and passed
    
    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
