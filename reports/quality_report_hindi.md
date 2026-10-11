# Hindi Dataset Quality Report

- Dataset File: `datasets/processed/hindi/hindi_clean.jsonl`
- Total Clean Records: **15,038**

## Class Distribution

| Class Label | Label Status | Count | Percentage |
| :--- | :--- | :--- | :--- |
| `fake` | `claimed_folder_label` | 5,089 | 33.84% |
| `real` | `claimed_folder_label` | 9,949 | 66.16% |

## Data Integrity Verification

- **UTF-8 Encoding**: Validated.
- **Unicode Normalization**: NFC enforced.
- **Exact Duplicates**: 0 duplicates present in accepted dataset.
- **Blank Text Bodies**: 0 blank records present.

## Manual Sample Review Findings

- **Sample Status**: COMPLETED (10 sampled records reviewed).
- **Unicode Devanagari Rendering**: Passed. Devanagari text rendered cleanly without garbled characters.
- **Header Menu Boilerplate**: Several `real` news articles contain prepended website navigation menus (*"हिन्दी ख़बरें दुनिया वीडियो देश क्राइम..."*). A regex cleaning step should be considered prior to model training.
- **Fact-Check Debunkers**: Some `fake` folder articles are fact-checking debunker reports explaining viral hoaxes.
