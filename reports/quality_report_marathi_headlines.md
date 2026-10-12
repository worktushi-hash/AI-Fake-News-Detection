# MARATHI_HEADLINES Dataset Quality Report

- Directory: `datasets/processed/marathi_headlines/`

## File Summaries

| Split File | Record Count | Task | Label Status |
| :--- | :--- | :--- | :--- |
| `marathi_headlines_train_clean.jsonl` | 9,643 | `marathi_headline_topic_classification` | `topic_category_not_veracity` |
| `marathi_headlines_train_no_leakage_clean.jsonl` | 9,640 | `marathi_headline_topic_classification` | `topic_category_not_veracity` |
| `marathi_headlines_valid_clean.jsonl` | 2,417 | `marathi_headline_topic_classification` | `topic_category_not_veracity` |
| `marathi_headlines_valid_no_leakage_clean.jsonl` | 2,415 | `marathi_headline_topic_classification` | `topic_category_not_veracity` |

## Data Integrity Verification

- **UTF-8 Encoding**: Validated.
- **Unicode Normalization**: NFC enforced.
- **Blank Text Bodies**: 0 blank records present.
