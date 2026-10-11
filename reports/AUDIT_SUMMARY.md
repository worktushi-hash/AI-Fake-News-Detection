# Dataset audit summary (read-only)

Generated from local files. Raw datasets were not modified. These numbers
come from running the scripts, not from guessed metrics.

## Environment

- Python: 3.12.12 (`C:\msys64\mingw64\bin\python.exe`)
- pandas / scikit-learn / PyTorch: not installed
- Audit scripts use the standard library only

## English (WELFake CSV)

- Records: 72,134
- Columns: unnamed index, `title`, `text`, `label`
- Label `0`: 35,028
- Label `1`: 37,106
- Blank titles: 558
- Blank texts: 783
- Unexpected labels: none
- Unique normalized article texts: 62,702
- Exact-text duplicate groups: 7,731
- Extra duplicate copies: 8,649
- Same text with different labels: 0
- **Label mapping: unverified** (see `welfake_label_mapping.md`)

## Hindi (folder corpus)

- Article `.txt` files: 20,593 (fake 10,293 / real 10,300)
- macOS artifacts skipped: 20,595
- Empty files: 0
- Short files (< 50 characters): 440
- Unique normalized texts: 15,052
- Duplicate groups: 2,838 (5,541 extra copies)
- Same text in both fake and real folders: **2 groups**
- Encoding: UTF-8 for all counted articles
- Folder names are claimed labels only; provenance is not yet documented

## Marathi (folder corpus)

- Article `.txt` files: 18,696 (fake 8,696 / real 10,000)
- macOS artifacts skipped: 18,698
- Empty files: 0
- Short files (< 50 characters): 341
- Unique normalized texts: 8,122
- Duplicate groups: 1,649 (10,574 extra copies)
- Same text in both fake and real folders: 0
- Encoding: UTF-8 for all counted articles
- Duplication is severe: fewer than half of the files are unique texts

## What this does *not* prove

- That folder labels are correct
- That Hindi vs Marathi language IDs are correct (both use Devanagari)
- That near-duplicate leakage is absent
- That WELFake `0`/`1` means fake/real

## Next human step

Confirm WELFake label mapping by reading a small sample of each class, then
decide how to keep one copy per duplicate group before any train/test split.
