# Manual Word-Level Language Annotation Guide for MaSaC Corpus

This guide explains how to manually mark/identify individual words in the MaSaC corpus as English (EN), Hindi (HI), or Other (OTHER).

## Overview

The MaSaC corpus already has automatic LID (Language Identification) tags at the word level, but we may want to manually verify or correct these annotations. This workflow provides tools to:

1. **Export** words for manual annotation
2. **Annotate** words in a spreadsheet
3. **Import** annotations back into the corpus format
4. **Validate** annotations for consistency

## Workflow

### Step 1: Export Words for Annotation

Export word-level data from the MaSaC corpus into a CSV file that's easy to edit:

```bash
python scripts/09_export_words_for_annotation.py
```

This creates `data/masac_raw/masac_words_for_annotation.csv` with columns:
- `file_id`: Audio file identifier
- `utterance_idx`: Index of utterance within the file
- `word_idx`: Position of word within utterance
- `word`: The actual word
- `language_tag`: Current language tag (EN, HI, OTHER, or UNK)
- `utterance_lang`: Utterance-level language (CSW, EN, HI)
- `transcript`: Full transcript for context

**Options:**
- `--input`: Specify input CSV (default: `data/masac_raw/masac_data_compiled.csv`)
- `--output`: Specify output CSV (default: `data/masac_raw/masac_words_for_annotation.csv`)
- `--subset N`: Process only first N utterances (useful for testing)

**Example:**
```bash
# Export all words
python scripts/09_export_words_for_annotation.py

# Export only first 100 utterances for testing
python scripts/09_export_words_for_annotation.py --subset 100
```

### Step 2: Manually Annotate Words

Open the exported CSV file in Excel, Google Sheets, or any spreadsheet editor:

1. **Edit the `language_tag` column** for each word:
   - `EN` for English words
   - `HI` for Hindi words
   - `OTHER` for punctuation, fillers, or other non-language tokens
   - `UNK` if you're unsure (can be fixed later)

2. **Use the `transcript` column** for context when deciding language tags

3. **Save the file** (keep CSV format)

**Tips:**
- You can filter by `utterance_lang` to focus on code-switched (CSW) utterances first
- Use Excel's find/replace for bulk corrections
- The `word_idx` column helps maintain word order

### Step 3: Import Annotations Back

After annotating, import the updated tags back into the corpus format:

```bash
python scripts/10_import_word_annotations.py \
    --input data/masac_raw/masac_words_for_annotation.csv \
    --original data/masac_raw/masac_data_compiled.csv \
    --output data/masac_raw/masac_data_compiled_manual.csv
```

This creates a new CSV file with updated `LID_tags` column containing your manual annotations.

**Options:**
- `--input`: Annotated word-level CSV
- `--original`: Original MaSaC CSV (default: `data/masac_raw/masac_data_compiled.csv`)
- `--output`: Output CSV with updated annotations (default: `data/masac_raw/masac_data_compiled_manual.csv`)

### Step 4: Validate Annotations (Optional)

Before using the annotated data, validate it for consistency:

```bash
python scripts/11_validate_word_annotations.py \
    --input data/masac_raw/masac_words_for_annotation.csv
```

This checks:
- All tags are valid (EN, HI, OTHER, UNK)
- Word counts match transcripts
- Consistency with utterance-level labels
- No unannotated words (UNK tags)

## Example Workflow

```bash
# 1. Export words (start with a small subset for testing)
python scripts/09_export_words_for_annotation.py --subset 10 \
    --output data/masac_raw/masac_words_sample.csv

# 2. Manually edit masac_words_sample.csv in Excel
#    Change language_tag column values as needed

# 3. Validate your annotations
python scripts/11_validate_word_annotations.py \
    --input data/masac_raw/masac_words_sample.csv

# 4. Import annotations back
python scripts/10_import_word_annotations.py \
    --input data/masac_raw/masac_words_sample.csv \
    --output data/masac_raw/masac_data_compiled_manual_sample.csv

# 5. Once validated, export full dataset
python scripts/09_export_words_for_annotation.py

# 6. Annotate full dataset, then import
python scripts/10_import_word_annotations.py \
    --input data/masac_raw/masac_words_for_annotation.csv \
    --output data/masac_raw/masac_data_compiled_manual.csv
```

## Language Tag Guidelines

### EN (English)
- English words: "hello", "the", "computer", "good"
- English proper nouns: "John", "London"
- English abbreviations: "TV", "OK", "USA"

### HI (Hindi)
- Hindi words: "hai", "mein", "kya", "aur"
- Hindi proper nouns: "Sahil", "Mumbai"
- Hindi words written in Roman script: "kaam", "ghar"

### OTHER
- Punctuation: ".", "!", "?", ",", ";"
- Fillers: "um", "uh", "hmm"
- Non-linguistic tokens: "hahaha", "haha"
- Ambiguous tokens that don't clearly belong to either language

### UNK (Unknown)
- Use temporarily when unsure
- Should be replaced with EN, HI, or OTHER before finalizing

## Notes

- **Word Tokenization**: Words are tokenized to match the original LID_tags format, which may split punctuation from words
- **Preserving Original Data**: The import script creates a new file, preserving the original `masac_data_compiled.csv`
- **Incremental Annotation**: You can annotate in batches and re-import multiple times
- **Validation**: Always validate before using annotated data in downstream analysis

## Troubleshooting

**Problem**: Word counts don't match between transcript and annotations
- **Solution**: Check if punctuation was tokenized correctly. The script splits punctuation from words.

**Problem**: Import fails with "KeyError"
- **Solution**: Ensure `file_id` and `utterance_idx` columns match between word CSV and original CSV.

**Problem**: Tags not updating in output file
- **Solution**: Verify the `language_tag` column contains valid values (EN, HI, OTHER, UNK) and check for typos.

## Related Scripts

- `scripts/00_explore_corpus_data.py`: Explore corpus structure
- `scripts/01_build_manifest.py`: Build manifest files for analysis
- `scripts/07_pilot_subset_selection.py`: Select subsets for pilot testing

