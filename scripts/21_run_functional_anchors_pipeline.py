#!/usr/bin/env python3
"""
Master pipeline script for functional anchors analysis.

This script runs the complete pipeline:
1. Detect discourse markers and repetitions
2. Extract switch directionality
3. Integrate all features
4. Run mixed-effects modeling
5. Generate reports
"""

import argparse
import pathlib
import subprocess
import sys

def run_step(script_name: str, args: list, description: str):
    """Run a pipeline step and handle errors."""
    print(f"\n{'='*80}")
    print(f"Step: {description}")
    print(f"Running: python {script_name} {' '.join(args)}")
    print(f"{'='*80}\n")
    
    script_path = pathlib.Path(__file__).parent / script_name
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return False
    
    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: Step failed with exit code {result.returncode}")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    print(result.stdout)
    if result.stderr:
        print("WARNINGS:", result.stderr)
    
    return True

def run_pipeline(corpus: str, manifest_file: str, feature_file: str,
                 word_file: str = None, output_dir: str = 'results/functional_anchors'):
    """
    Run the complete functional anchors analysis pipeline.
    """
    print(f"\n{'='*80}")
    print(f"Functional Anchors Analysis Pipeline: {corpus.upper()}")
    print(f"{'='*80}\n")
    
    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Detect discourse markers and repetitions
    manifest_annotated = output_path / f"{corpus}_manifest_with_anchors.csv"
    if not run_step(
        '16_detect_discourse_markers_repetitions.py',
        ['--manifest', manifest_file, '--output', str(manifest_annotated), '--corpus', corpus],
        'Detecting discourse markers and repetitions'
    ):
        print("Pipeline stopped at Step 1")
        return False
    
    # Step 2: Extract switch directionality
    manifest_with_direction = output_path / f"{corpus}_manifest_with_direction.csv"
    direction_args = ['--manifest', str(manifest_annotated), 
                     '--output', str(manifest_with_direction), '--corpus', corpus]
    if word_file:
        direction_args.extend(['--words', word_file])
    
    if not run_step(
        '17_extract_switch_directionality.py',
        direction_args,
        'Extracting switch directionality'
    ):
        print("Pipeline stopped at Step 2")
        return False
    
    # Step 3: Preprocess speaker/interaction metadata
    manifest_with_metadata = output_path / f"{corpus}_manifest_with_metadata.csv"
    if not run_step(
        "28_preprocess_speaker_interaction_metadata.py",
        [
            "--manifest-in",
            str(manifest_with_direction),
            "--manifest-out",
            str(manifest_with_metadata),
            "--corpus",
            corpus,
        ],
        "Preprocessing speaker and interaction metadata",
    ):
        print("Pipeline stopped at Step 3")
        return False

    # Step 4: Integrate all features
    integrated_file = output_path / f"{corpus}_integrated_features.csv"
    if not run_step(
        '19_integrate_features_for_analysis.py',
        ['--features', feature_file, '--manifest', str(manifest_with_metadata),
         '--output', str(integrated_file), '--corpus', corpus],
        'Integrating all features'
    ):
        print("Pipeline stopped at Step 4")
        return False
    
    # Step 5: Run mixed-effects modeling
    me_output_dir = output_path / 'mixed_effects'
    if not run_step(
        '18_mixed_effects_analysis.py',
        ['--features', feature_file, '--manifest', str(manifest_with_metadata),
         '--output-dir', str(me_output_dir), '--corpus', corpus, '--n-features', '10'],
        'Running mixed-effects modeling'
    ):
        print("Pipeline stopped at Step 5 (non-fatal, continuing...)")
    
    # Step 6: Generate functional anchors report
    report_file = output_path / f"{corpus}_functional_anchors_report.md"
    if not run_step(
        '20_generate_functional_anchors_report.py',
        ['--integrated', str(integrated_file), '--output', str(report_file), '--corpus', corpus],
        'Generating functional anchors report'
    ):
        print("Pipeline stopped at Step 6")
        return False
    
    print(f"\n{'='*80}")
    print("Pipeline completed successfully!")
    print(f"{'='*80}\n")
    print(f"Output directory: {output_path}")
    print(f"\nGenerated files:")
    print(f"  - Annotated manifest: {manifest_annotated}")
    print(f"  - Manifest with directionality: {manifest_with_direction}")
    print(f"  - Manifest with metadata: {manifest_with_metadata}")
    print(f"  - Integrated features: {integrated_file}")
    print(f"  - Functional anchors report: {report_file}")
    if me_output_dir.exists():
        print(f"  - Mixed-effects results: {me_output_dir}")
    
    return True

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Run complete functional anchors analysis pipeline'
    )
    p.add_argument('--corpus', type=str, choices=['seame', 'masac'],
                   required=True, help='Corpus name')
    p.add_argument('--manifest', type=str, required=True,
                   help='Input manifest CSV file')
    p.add_argument('--features', type=str, required=True,
                   help='Input prosodic features CSV file')
    p.add_argument('--words', type=str, default=None,
                   help='Optional word-level CSV (for MASAC directionality)')
    p.add_argument('--output-dir', type=str, 
                   default='results/functional_anchors',
                   help='Output directory')
    
    args = p.parse_args()
    
    manifest_file = pathlib.Path(args.manifest)
    feature_file = pathlib.Path(args.features)
    
    if not manifest_file.exists():
        print(f"ERROR: Manifest file not found: {manifest_file}")
        exit(1)
    
    if not feature_file.exists():
        print(f"ERROR: Feature file not found: {feature_file}")
        exit(1)
    
    success = run_pipeline(
        args.corpus, str(manifest_file), str(feature_file),
        args.words, args.output_dir
    )
    
    sys.exit(0 if success else 1)
