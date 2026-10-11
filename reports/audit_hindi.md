# Hindi folder corpus audit

Raw files were not modified.

- Article `.txt` files counted: **20593**
- macOS/OS artifacts skipped: **20595**
- Claimed fake: **10293**
- Claimed real: **10300**
- Unknown folder label: **0**
- Empty files: **0**
- Short files (< 50 chars): **440**
- Unique normalized texts: **15052**
- Duplicate groups: **2838**
- Extra duplicate copies: **5541**
- Same text, different folder labels: **2**
- Decode-with-replacement files: **0**
- Low Devanagari ratio files: **22**
- Files containing `http://` or `https://`: **197**

## Encodings

- `utf-8-sig`: 20593

## Notes

- Folder names are treated as claimed labels, not verified ground truth.
- Hindi and Marathi both use Devanagari; script ratio is not a language ID.
- Exact-hash duplicates do not prove that near-duplicates or leakage are absent.
- __MACOSX and ._* files are OS artifacts and were not counted as articles.

## Example conflicting-label groups

- hash `415f75b77451...` count=2 labels=['fake', 'real']
  - Hindi_fake_news/Hindi_fake_news (10202).txt
  - Hindi_real_news/Hindi_real_news (7403).txt
- hash `1dbdcab3eb04...` count=2 labels=['fake', 'real']
  - Hindi_fake_news/Hindi_fake_news (10203).txt
  - Hindi_real_news/Hindi_real_news (7409).txt
