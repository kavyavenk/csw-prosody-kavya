"""
Corpus Comparison Report Generator

Compares SEAME and MASAC corpora characteristics for prosody replication study.
Generates a comprehensive report comparing data availability, distributions, and suitability.
"""

import argparse
import pandas as pd
import pathlib
import numpy as np
from collections import Counter

p = argparse.ArgumentParser(description="Generate corpus comparison report")
p.add_argument("--output", type=str, default="reports/corpus_comparison.md",
               help="Output report file (default: reports/corpus_comparison.md)")
args = p.parse_args()

OUT_DIR = pathlib.Path("reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = pathlib.Path(args.output)

print("Generating corpus comparison report...\n")

# Load exploration data if available
seame_file = OUT_DIR / "seame_exploration.csv"
masac_file = OUT_DIR / "masac_exploration.csv"

reports = {}

# SEAME Analysis
if seame_file.exists():
    print(f"Loading SEAME data: {seame_file}")
    df_seame = pd.read_csv(seame_file)
    reports['seame'] = {
        'name': 'SEAME',
        'languages': 'Mandarin-English',
        'data': df_seame
    }
else:
    print(f"SEAME exploration file not found. Run: python scripts/00_explore_corpus_data.py --corpus seame")
    reports['seame'] = None

# MASAC Analysis
if masac_file.exists():
    print(f"Loading MASAC data: {masac_file}")
    df_masac = pd.read_csv(masac_file)
    reports['masac'] = {
        'name': 'MASAC',
        'languages': 'Hindi-English',
        'data': df_masac
    }
else:
    print(f"MASAC exploration file not found. Run: python scripts/00_explore_corpus_data.py --corpus masac")
    reports['masac'] = None

# Generate report
report_lines = []
report_lines.append("# Corpus Comparison Report: SEAME vs MASAC")
report_lines.append("")
report_lines.append("Generated for prosody replication study based on Spanish-English CSW paper methodology.")
report_lines.append("")
report_lines.append("---")
report_lines.append("")

# Overview
report_lines.append("## 1. Overview")
report_lines.append("")
report_lines.append("| Corpus | Language Pair | Speech Style | Target Use Case |")
report_lines.append("|--------|---------------|--------------|----------------|")
report_lines.append("| SEAME | Mandarin-English | Spontaneous conversation | Tonal language comparison |")
report_lines.append("| MASAC | Hindi-English | Conversational + tasks | Non-tonal language comparison |")
report_lines.append("")

# Data Availability
report_lines.append("## 2. Data Availability")
report_lines.append("")

for corpus_key, corpus_info in reports.items():
    if corpus_info is None:
        continue
    
    name = corpus_info['name']
    df = corpus_info['data']
    
    report_lines.append(f"### {name}")
    report_lines.append("")
    
    # Basic stats
    total_utts = len(df)
    report_lines.append(f"- **Total utterances**: {total_utts:,}")
    
    # Language distribution
    if 'language' in df.columns:
        lang_dist = df['language'].value_counts()
        report_lines.append(f"- **Language distribution**:")
        for lang, count in lang_dist.items():
            pct = 100 * count / total_utts
            report_lines.append(f"  - {lang}: {count:,} ({pct:.1f}%)")
    elif 'Language' in df.columns:
        lang_dist = df['Language'].value_counts()
        report_lines.append(f"- **Language distribution**:")
        for lang, count in lang_dist.items():
            pct = 100 * count / total_utts
            report_lines.append(f"  - {lang}: {count:,} ({pct:.1f}%)")
    
    # Speakers
    if 'speaker' in df.columns:
        n_speakers = df['speaker'].nunique()
        report_lines.append(f"- **Unique speakers**: {n_speakers}")
    
    # Duration
    if 'duration_sec' in df.columns:
        mean_dur = df['duration_sec'].mean()
        median_dur = df['duration_sec'].median()
        total_hours = df['duration_sec'].sum() / 3600
        report_lines.append(f"- **Mean utterance duration**: {mean_dur:.2f}s")
        report_lines.append(f"- **Median utterance duration**: {median_dur:.2f}s")
        report_lines.append(f"- **Total duration**: {total_hours:.1f} hours")
    
    # Code-switching
    if 'number_of_code_switches' in df.columns:
        cs_utts = (df['number_of_code_switches'] > 0).sum()
        report_lines.append(f"- **CS utterances**: {cs_utts:,} ({100*cs_utts/total_utts:.1f}%)")
    elif 'Language' in df.columns:
        cs_utts = (df['Language'] == 'CSW').sum()
        report_lines.append(f"- **CS utterances**: {cs_utts:,} ({100*cs_utts/total_utts:.1f}%)")
    
    # Audio files
    wav_dir = pathlib.Path(f"data/{corpus_key}_wav16k")
    if wav_dir.exists():
        n_wavs = len(list(wav_dir.rglob("*.wav")))
        report_lines.append(f"- **Audio files available**: {n_wavs:,}")
    
    report_lines.append("")

# Comparison Table
report_lines.append("## 3. Direct Comparison")
report_lines.append("")

if reports['seame'] and reports['masac']:
    df_seame = reports['seame']['data']
    df_masac = reports['masac']['data']
    
    comparison_rows = []
    
    # Total utterances
    comparison_rows.append(("Total utterances", len(df_seame), len(df_masac)))
    
    # CS percentage
    if 'number_of_code_switches' in df_seame.columns:
        seame_cs = (df_seame['number_of_code_switches'] > 0).sum()
        seame_cs_pct = 100 * seame_cs / len(df_seame)
    elif 'language' in df_seame.columns:
        seame_cs = (df_seame['language'] == 'CS').sum()
        seame_cs_pct = 100 * seame_cs / len(df_seame)
    else:
        seame_cs_pct = "N/A"
    
    if 'Language' in df_masac.columns:
        masac_cs = (df_masac['Language'] == 'CSW').sum()
        masac_cs_pct = 100 * masac_cs / len(df_masac)
    else:
        masac_cs_pct = "N/A"
    
    comparison_rows.append(("CS percentage", f"{seame_cs_pct:.1f}%", f"{masac_cs_pct:.1f}%"))
    
    # Duration
    if 'duration_sec' in df_seame.columns and 'duration_sec' in df_masac.columns:
        seame_mean = df_seame['duration_sec'].mean()
        masac_mean = df_masac['duration_sec'].mean() if 'duration_sec' in df_masac.columns else "N/A"
        comparison_rows.append(("Mean duration (s)", f"{seame_mean:.2f}", 
                               f"{masac_mean:.2f}" if isinstance(masac_mean, float) else masac_mean))
    
    # Speakers
    if 'speaker' in df_seame.columns:
        seame_spk = df_seame['speaker'].nunique()
        comparison_rows.append(("Unique speakers", seame_spk, "N/A" if 'speaker' not in df_masac.columns else df_masac['speaker'].nunique()))
    
    report_lines.append("| Metric | SEAME | MASAC |")
    report_lines.append("|--------|-------|-------|")
    for metric, seame_val, masac_val in comparison_rows:
        report_lines.append(f"| {metric} | {seame_val} | {masac_val} |")
    report_lines.append("")

# Methodology Alignment
report_lines.append("## 4. Methodology Alignment with Spanish-English Study")
report_lines.append("")
report_lines.append("### Requirements from Spanish-English Paper:")
report_lines.append("")
report_lines.append("1. **Spontaneous speech**: ✓ Both corpora contain spontaneous/conversational speech")
report_lines.append("2. **Token-level LID**: ✓ Both have language identification at utterance/token level")
report_lines.append("3. **Speaker metadata**: ✓ Demographic information available")
report_lines.append("4. **DisVoice compatibility**: ✓ Audio can be standardized to 16kHz mono")
report_lines.append("5. **Balanced conditions**: Need to verify CS vs. monolingual balance")
report_lines.append("")

# Recommendations
report_lines.append("## 5. Recommendations for Pilot Testing")
report_lines.append("")
report_lines.append("### SEAME:")
report_lines.append("- Focus on tonal language effects on prosody")
report_lines.append("- Compare CS vs. monolingual Mandarin vs. monolingual English")
report_lines.append("- Examine if tonal features interact with prosodic variation")
report_lines.append("")
report_lines.append("### MASAC:")
report_lines.append("- Focus on non-tonal language comparison (parallel to Spanish-English)")
report_lines.append("- Compare CS vs. monolingual Hindi vs. monolingual English")
report_lines.append("- Validate if duration > energy > pitch pattern replicates")
report_lines.append("")
report_lines.append("### Pilot Subset Selection:")
report_lines.append("- Start with 100-200 utterances per condition")
report_lines.append("- Ensure speaker balance across conditions")
report_lines.append("- Filter by duration: 0.5s - 10s")
report_lines.append("- Verify audio file availability")
report_lines.append("")

# Next Steps
report_lines.append("## 6. Next Steps")
report_lines.append("")
report_lines.append("1. Run pilot subset selection:")
report_lines.append("   ```bash")
report_lines.append("   python scripts/07_pilot_subset_selection.py --corpus seame --n_per_condition 100")
report_lines.append("   python scripts/07_pilot_subset_selection.py --corpus masac --n_per_condition 100")
report_lines.append("   ```")
report_lines.append("")
report_lines.append("2. Extract audio clips:")
report_lines.append("   ```bash")
report_lines.append("   python scripts/02_slice_by_timestamps.py --corpus seame")
report_lines.append("   python scripts/02_slice_by_timestamps.py --corpus masac")
report_lines.append("   ```")
report_lines.append("")
report_lines.append("3. Extract DisVoice features:")
report_lines.append("   ```bash")
report_lines.append("   python scripts/03_extract_disvoice_utterance.py --corpus seame")
report_lines.append("   python scripts/03_extract_disvoice_utterance.py --corpus masac")
report_lines.append("   ```")
report_lines.append("")
report_lines.append("4. Run statistical comparisons:")
report_lines.append("   ```bash")
report_lines.append("   python scripts/04_first_contrasts.py --corpus seame")
report_lines.append("   python scripts/04_first_contrasts.py --corpus masac")
report_lines.append("   ```")
report_lines.append("")

# Write report
with open(REPORT_FILE, 'w') as f:
    f.write('\n'.join(report_lines))

print(f"Report saved to: {REPORT_FILE}")
print("\nComparison report complete!")

