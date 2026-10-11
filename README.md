# AI-Powered Fake News Detection for Regional Languages

A text-based fake news detection system and dataset package for English, Hindi, and Marathi.

---

## Current Status: Final Dataset Preparation Complete

The dataset cleaning, deduplication, quarantine, and validation pipeline is fully built and executed. All processed datasets follow a unified JSONL schema and are ready for model baselines.

---

## How to Reproduce the Full Pipeline

Requirements: Standard Python 3.10+ library (no external third-party dependencies required for dataset preparation).

Run tests, raw file integrity check, cleaning pipeline, automated validation, and report generation in a single command:

```powershell
python scripts/run_pipeline.py
```

To run individual pipeline steps:

```powershell
# 1. Run unit tests
python -m unittest discover -s tests -v

# 2. Check raw file SHA-256 integrity
python scripts/verify_raw_integrity.py

# 3. Run cleaning and quarantine pipeline
python scripts/clean_dataset_pipeline.py

# 4. Run automated validation checks
python scripts/validate_processed_datasets.py

# 5. Draw reproducible quality samples
python scripts/sample_quality_review.py
```

---

## Dataset Package Summary

| Language | Raw Records | Processed Clean | Quarantined | Excluded | Output Path | Format |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **English** | 72,134 | 62,702 | 0 | 9,432 | `datasets/processed/english/english_clean.jsonl` | JSONL |
| **Hindi** | 20,593 | 15,038 | 26 | 26,124 | `datasets/processed/hindi/hindi_clean.jsonl` | JSONL |
| **Marathi** | 18,696 | 8,122 | 0 | 29,272 | `datasets/processed/marathi/marathi_clean.jsonl` | JSONL |
| **Quarantine** | - | - | **26** | - | `datasets/quarantine/quarantined_records.jsonl` | JSONL |

---

## Unified Processed Output Schema

Every clean record in `datasets/processed/<lang>/<lang>_clean.jsonl` adheres to the following JSON schema:

```json
{
  "id": "en_000001",
  "language": "en",
  "title": "Article Title or null",
  "text": "Cleaned article text body.",
  "label": "0",
  "source_dataset": "WELFake",
  "source_record_id": "1",
  "source_label": "0",
  "label_source": "WELFake_Dataset.csv",
  "label_status": "unverified",
  "review_status": "accepted"
}
```

---

## Key Data Quality Policies

1. **Raw Data Inviolability**: Raw datasets under `datasets/raw/` are strictly read-only; pre- and post-run SHA-256 hashes are verified in `reports/raw_file_integrity.md`.
2. **Exact Deduplication**: Exactly 1 canonical record per identical NFC-normalized text is accepted. Duplicate copies are excluded.
3. **Conflicting Label Quarantine**: Duplicate texts spanning multiple labels are routed to `datasets/quarantine/quarantined_records.jsonl`.
4. **WELFake Label Status**: Raw `0`/`1` labels are preserved as `source_label`. The label mapping remains marked as `unverified` in accordance with Zenodo metadata conflict notes (`reports/welfake_label_mapping.md`).

---

## GitHub Tracking & Large File Guidance

- **Tracked in Git**:
  - `scripts/`: Cleaning, audit, validation, and pipeline scripts.
  - `reports/`: Markdown and JSON audit/quality reports.
  - `tests/`: Automated unit and pipeline tests.
  - `README.md`, `.gitignore`, `requirements.txt`
- **Gitignored Datasets**:
  - `datasets/raw/`: Raw files stay local.
  - `datasets/processed/english/english_clean.jsonl` (219.7 MB) and `datasets/processed/hindi/hindi_clean.jsonl` (133.2 MB) exceed GitHub's standard 100 MB per-file limit.
  - If committing processed datasets to remote repositories, enable **Git LFS** (`git lfs track "*.jsonl"`), or regenerate them on target environments by running `python scripts/run_pipeline.py`.

---

## Data and Reproducibility

Original datasets are kept outside version control until their contents, licensing, and suitability have been reviewed. No model performance results will be reported until experiments have actually been conducted.

---

## Repository Structure

- `datasets/`: Processed JSONL files and quarantine storage.
- `reports/`: Audit, policy, quality, and validation reports.
- `scripts/`: Modular Python scripts for pipeline execution.
- `tests/`: Unit and pipeline integration tests.
