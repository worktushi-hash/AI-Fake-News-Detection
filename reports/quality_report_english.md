# English Dataset Quality Report

- Dataset File: `datasets/processed/english/english_clean.jsonl`
- Total Clean Records: **62,702**

## Class Distribution

| Class Label | Label Status | Count | Percentage |
| :--- | :--- | :--- | :--- |
| `0` | `unverified` | 30,551 | 48.72% |
| `1` | `unverified` | 32,151 | 51.28% |

## Data Integrity Verification

- **UTF-8 Encoding**: Validated.
- **Unicode Normalization**: NFC enforced.
- **Exact Duplicates**: 0 duplicates present in accepted dataset.
- **Blank Text Bodies**: 0 blank records present.

## Manual Sample Review Findings

- **Sample Status**: COMPLETED (10 sampled records reviewed).
- **Text Readability**: Passed. Titles and article bodies render cleanly with preserved punctuation.
- **Label Uncertainty Note**: Label `0` samples consist of wire-service Reuters news, while `1` samples consist of opinion blogs and clickbait. Target labels remain marked as `unverified` due to Zenodo documentation conflicts.
