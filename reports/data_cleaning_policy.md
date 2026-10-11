# Data Cleaning and Preprocessing Policy

This document defines the transparent, conservative, and auditable cleaning policy for the **AI-Powered Fake News Detection** project across English, Hindi, and Marathi datasets.

---

## 1. Core Principles

1. **Raw Data Inviolability**: Original raw dataset files under `datasets/raw/` are strictly read-only and must never be modified, renamed, or deleted.
2. **Deterministic Processing**: All cleaning and processing operations are deterministic and reproducible.
3. **No Unexplained Exclusions**: Every excluded or quarantined record must be tracked with a specific reason code, source record identifier, and count.
4. **Conservation of Information**: Missing titles, URLs, or non-standard punctuation do not justify record deletion if the article text body is intact and usable. No translation or content paraphrasing is permitted.

---

## 2. Record Exclusion & Quarantine Criteria

A raw record is categorized into one of three dispositions:
- `accepted`: Meets all quality and uniqueness criteria; placed into `datasets/processed/<lang>/<lang>_clean.jsonl`.
- `quarantined`: Valid text present, but assigned label is conflicting or ground-truth is uncertain; placed into `datasets/quarantine/quarantined_records.jsonl`.
- `excluded`: Fails minimum quality or usability criteria (e.g., missing text body, non-article OS artifact); logged in `reports/exclusion_quarantine_summary.md`.

### Specific Rule Definitions

| Issue / Condition | Disposition | Reason Code | Policy Rule |
| :--- | :--- | :--- | :--- |
| Empty / whitespace-only text | `excluded` | `blank_text` | Records with empty or zero-character text bodies after stripping are excluded. |
| Missing title | `accepted` | N/A | Missing titles are preserved as `null` in the schema. The record is retained if `text` is valid. |
| Short text (< 50 characters) | `accepted` | N/A | Articles shorter than 50 characters are NOT automatically discarded. They are preserved, and logged in quality reports. |
| URLs in text | `accepted` | N/A | URLs are preserved in the text body. They are not stripped nor treated as grounds for removal. |
| macOS / OS artifacts (`._*`, `__MACOSX`, `.DS_Store`) | `excluded` | `os_artifact` | Unzip leftovers and OS artifacts are skipped and logged. |
| Non-target language / Script mismatch | `quarantined` | `script_mismatch` | Articles with letter count ≥ 20 where target script ratio is < 50% (e.g. non-Devanagari text in Hindi/Marathi corpus) are quarantined. |
| Exact duplicate (Same label) | `accepted` (1 copy) / `excluded` (copies) | `exact_duplicate` | The first canonical record is accepted; subsequent identical text copies are deduplicated and logged. |
| Exact duplicate (Conflicting labels) | `quarantined` | `conflicting_labels` | All copies in exact duplicate groups spanning different labels (e.g., `fake` AND `real`) are quarantined. |
| Unverified / Ambiguous Label Mapping | `accepted` (with note) / `quarantined` | `unverified_label` | For English (WELFake), raw labels (`0`/`1`) are retained as `source_label` and target `label` is marked as `unverified` in provenance fields. |

---

## 3. Text Normalization Standards

- **Unicode Normalization**: All text is normalized using **Unicode NFC** (`unicodedata.normalize("NFC", text)`).
- **Whitespace Collapsing**: Multiple consecutive whitespace characters (spaces, tabs, non-breaking spaces) within text lines are collapsed into a single space (`" ".join(text.split())`).
- **Punctuation & Script Preservation**: All Devanagari characters, Latin characters, numbers, standard punctuation, and quotes are strictly preserved. No stop-word removal or stemming is performed at the dataset preparation stage.

---

## 4. Deduplication & Near-Duplicate Policy

### 4.1 Exact Deduplication
- **Scope**: Computed per language using SHA-256 hashes of NFC-normalized, whitespace-collapsed text.
- **Handling**:
  - If all records in a duplicate group share the same label, the record with the earliest original ID is retained as the canonical accepted record.
  - If records in a duplicate group have conflicting labels (e.g., same text in `Hindi_fake_news` and `Hindi_real_news`), all records in that group are routed to quarantine.

### 4.2 Near-Duplicate Analysis
- **Scope**: Near-duplicate candidates are detected using MinHash signatures (128 permutation hashes) with 5-character shingling and Jaccard similarity threshold $J \ge 0.85$.
- **Handling**: Near-duplicate groups are audited and documented in `reports/duplicate_analysis.md`. Non-identical texts are NOT automatically discarded without direct evidence of corruption or template duplication.

---

## 5. Output Schema Definition

Every accepted record in `datasets/processed/<lang>/<lang>_clean.jsonl` adheres to the following unified JSON schema:

```json
{
  "id": "en_000001",
  "language": "en",
  "title": "Article Title or null",
  "text": "Full cleaned text body of the article.",
  "label": "0",
  "source_dataset": "WELFake",
  "source_record_id": "1",
  "source_label": "0",
  "label_source": "WELFake_Dataset.csv",
  "label_status": "unverified",
  "review_status": "accepted"
}
```

Every quarantined record in `datasets/quarantine/quarantined_records.jsonl` includes:

```json
{
  "id": "hi_q000001",
  "language": "hi",
  "title": null,
  "text": "Article text body",
  "source_dataset": "Hindi_corpus",
  "source_record_id": "Hindi_fake_news (10202).txt",
  "source_label": "fake",
  "review_status": "quarantined",
  "quarantine_reason": "conflicting_labels",
  "quarantine_details": "Exact text appears in both Hindi_fake_news and Hindi_real_news"
}
```
