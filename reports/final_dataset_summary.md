# Final Dataset Summary Report

This report presents the final counts, class distributions, and output locations for the AI-Powered Fake News Detection dataset package.

## Summary Table

| Language | Raw Records | Processed Clean | Quarantined | Excluded | Output Path | Format |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| English | 72,134 | 62,702 | 0 | 9,432 | `datasets/processed/english/english_clean.jsonl` | JSONL |
| Hindi | 20,593 | 15,038 | 26 | 26,124 | `datasets/processed/hindi/hindi_clean.jsonl` | JSONL |
| Marathi | 18,696 | 8,122 | 0 | 29,272 | `datasets/processed/marathi/marathi_clean.jsonl` | JSONL |

## Quarantined Summary

- Quarantined File: `datasets/quarantine/quarantined_records.jsonl`
- Total Quarantined Records: **26**
- Reasons: 22 low Devanagari script ratio, 4 conflicting folder labels.

## Ground-Truth Status Notes

1. **English (WELFake)**: Label mapping is documented as `unverified` due to contradictory Zenodo metadata statements.
2. **Hindi & Marathi**: Folder labels are preserved as `claimed_folder_label`.
