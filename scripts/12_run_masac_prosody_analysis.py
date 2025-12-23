#!/usr/bin/env python3
"""
Run full MASAC prosody analysis pipeline to replicate Spanish-English findings.

This script runs the complete pipeline:
1. Build manifest from word-level annotations
2. Extract DisVoice prosodic features
3. Run statistical comparisons
4. Generate summary report

Usage:
    python scripts/12_run_masac_prosody_analysis.py [--words WORD_CSV] [--full]
"""

import argparse
import pathlib
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        print(f"Exit code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError as e:
        print(f"ERROR: Command not found. Make sure all dependencies are installed.")
        print(f"Missing: {e}")
        return False

def main():
    p = argparse.ArgumentParser(description='Run full MASAC prosody analysis pipeline')
    p.add_argument('--words', type=str,
                   default='data/masac_raw/masac_words_sample.csv',
                   help='Word-level CSV with language tags')
    p.add_argument('--full', action='store_true',
                   help='Use full dataset instead of sample')
    p.add_argument('--skip-manifest', action='store_true',
                   help='Skip manifest building (use existing)')
    p.add_argument('--skip-slice', action='store_true',
                   help='Skip audio slicing (use existing clips)')
    p.add_argument('--skip-features', action='store_true',
                   help='Skip feature extraction (use existing features)')
    
    args = p.parse_args()
    
    if args.full:
        # Use full dataset - would need to export from masac_data_compiled.csv
        print("Full dataset mode: This would require exporting word-level annotations")
        print("from masac_data_compiled.csv. Using sample for now.")
        print("To use full dataset, first run:")
        print("  python scripts/09_export_words_for_annotation.py")
        print("  # Then manually annotate and update language tags")
        print("  python scripts/12_run_masac_prosody_analysis.py --words <updated_csv>")
    
    word_file = pathlib.Path(args.words)
    if not word_file.exists():
        print(f"ERROR: Word file not found: {word_file}")
        sys.exit(1)
    
    print("="*60)
    print("MASAC Prosody Analysis Pipeline")
    print("Replicating Spanish-English CSW Prosody Findings")
    print("="*60)
    
    # Step 1: Build manifest
    if not args.skip_manifest:
        success = run_command([
            sys.executable, "scripts/01_build_manifest_masac_from_words.py",
            "--words", str(word_file),
            "--output", "manifests/masac_manifest.csv",
            "--no-durations"
        ], "Build MASAC manifest from word-level annotations")
        
        if not success:
            print("\nERROR: Manifest building failed. Cannot continue.")
            sys.exit(1)
    else:
        print("\nSkipping manifest building (using existing)")
    
    # Step 2: Slice audio (if needed)
    if not args.skip_slice:
        success = run_command([
            sys.executable, "scripts/02_slice_by_timestamps.py",
            "--corpus", "masac"
        ], "Slice audio files into utterance clips")
        
        if not success:
            print("\nWARNING: Audio slicing failed. This may be OK if:")
            print("  - Audio files are not available yet")
            print("  - Files are already individual utterances")
            print("Continuing with feature extraction...")
    else:
        print("\nSkipping audio slicing (using existing clips)")
    
    # Step 3: Extract DisVoice features
    if not args.skip_features:
        success = run_command([
            sys.executable, "scripts/03_extract_disvoice_utterance.py",
            "--corpus", "masac"
        ], "Extract DisVoice prosodic features")
        
        if not success:
            print("\nERROR: Feature extraction failed.")
            print("This requires:")
            print("  1. Audio files in data/masac_wav16k/ or data/masac_wav16k_clips/")
            print("  2. DisVoice library installed: pip install disvoice")
            sys.exit(1)
    else:
        print("\nSkipping feature extraction (using existing features)")
    
    # Step 4: Run statistical comparisons
    success = run_command([
        sys.executable, "scripts/04_first_contrasts.py",
        "--corpus", "masac"
    ], "Run statistical comparisons (t-tests with FDR correction)")
    
    if not success:
        print("\nERROR: Statistical analysis failed.")
        print("This requires features to be extracted first.")
        sys.exit(1)
    
    # Step 5: Generate summary report
    print("\n" + "="*60)
    print("Analysis Complete!")
    print("="*60)
    print("\nResults are in:")
    print("  - features/first_contrast_masac.csv")
    print("\nTo view results:")
    print("  python scripts/05_plot_quick.py --corpus masac")
    print("\nTo compare with Spanish-English findings, see:")
    print("  - METHODOLOGY.md (for expected patterns)")
    print("  - features/first_contrast_masac.csv (for actual results)")

if __name__ == '__main__':
    main()

