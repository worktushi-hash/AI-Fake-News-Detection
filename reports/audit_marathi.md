# Marathi folder corpus audit

Raw files were not modified.

- Article `.txt` files counted: **18696**
- macOS/OS artifacts skipped: **18698**
- Claimed fake: **8696**
- Claimed real: **10000**
- Unknown folder label: **0**
- Empty files: **0**
- Short files (< 50 chars): **341**
- Unique normalized texts: **8122**
- Duplicate groups: **1649**
- Extra duplicate copies: **10574**
- Same text, different folder labels: **0**
- Decode-with-replacement files: **0**
- Low Devanagari ratio files: **0**
- Files containing `http://` or `https://`: **87**

## Encodings

- `utf-8-sig`: 18696

## Notes

- Folder names are treated as claimed labels, not verified ground truth.
- Hindi and Marathi both use Devanagari; script ratio is not a language ID.
- Exact-hash duplicates do not prove that near-duplicates or leakage are absent.
- __MACOSX and ._* files are OS artifacts and were not counted as articles.

## Example conflicting-label groups

None found among exact-hash duplicates.
