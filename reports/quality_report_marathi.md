# Marathi Dataset Quality Report

- Dataset File: `datasets/processed/marathi/marathi_clean.jsonl`
- Total Clean Records: **8,122**

## Class Distribution

| Class Label | Label Status | Count | Percentage |
| :--- | :--- | :--- | :--- |
| `fake` | `claimed_folder_label` | 3,100 | 38.17% |
| `real` | `claimed_folder_label` | 5,022 | 61.83% |

## Data Integrity Verification

- **UTF-8 Encoding**: Validated.
- **Unicode Normalization**: NFC enforced.
- **Exact Duplicates**: 0 duplicates present in accepted dataset.
- **Blank Text Bodies**: 0 blank records present.

## Manual Sample Review Findings

- **Sample Status**: COMPLETED (10 sampled records reviewed).
- **Unicode Devanagari Rendering**: Passed. Marathi Devanagari text rendered cleanly with correct vocabulary.
- **Header Menu Boilerplate**: Minor news portal navigation header text present at start of some `real` news bodies.
