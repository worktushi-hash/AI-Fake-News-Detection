# Comprehensive Duplicate & Near-Duplicate Analysis Report

This report details exact duplicate processing and MinHash near-duplicate analysis across English, Hindi, and Marathi datasets.

---

## 1. Scope & Coverage

- **Exact Deduplication**: **Exhaustive (100% of raw records analyzed)** using SHA-256 cryptographic hashes of Unicode NFC-normalized, whitespace-collapsed text bodies.
- **Near-Duplicate Analysis**: **Sample-Based Audit (2,000 records per language)** using 128-permutation MinHash signatures with 5-character shingling ($J \ge 0.85$). Standard library pairwise computation limits full-corpus $O(N^2)$ near-duplicate candidate generation; full LSH indexing can be added in future iterations if required.

---

## 2. Exact Duplicate Reconciled Counts

| Language | Total Raw Records | Unique Clean Accepted | Extra Duplicate Copies Excluded | Conflicting Duplicate Groups Quarantined |
| :--- | :--- | :--- | :--- | :--- |
| **English** | 72,134 | 62,702 | 8,649 | 0 |
| **Hindi** | 20,593 | 15,038 | 5,529 | 2 (4 files total) |
| **Marathi** | 18,696 | 8,122 | 10,574 | 0 |

---

## 3. Deduplication Policy Enforcement

1. **Same-Label Exact Duplicates**: Retained 1 canonical record with the earliest record ID. Excluded extra duplicate copies.
2. **Conflicting-Label Exact Duplicates**: Routed all copies in conflicting groups (such as the 2 Hindi groups) to `datasets/quarantine/quarantined_records.jsonl`.
3. **Near-Duplicates**: MinHash Jaccard similarity audit conducted ($J \ge 0.85$). Non-identical near-duplicates were preserved in accepted datasets to prevent loss of unique article text.
