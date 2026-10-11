# WELFake Label Mapping Report: Unresolved Ground-Truth Status

**Current Status: UNRESOLVED / UNVERIFIED.**

This document details the conflicting documentation and metadata regarding the label convention in the WELFake dataset (`datasets/raw/english/WELFake_Dataset.csv`).

---

## 1. Discrepancy Overview

The published WELFake dataset repository (Zenodo Record [4561253](https://zenodo.org/records/4561253) by Verma et al., 2021) contains two contradictory statements:

1. **Class Count Statement**: *"The dataset has 35,028 real and 37,106 fake articles."*
2. **Legend Statement**: *"The label column is 0 = fake and 1 = real."*

In the local raw CSV file (`WELFake_Dataset.csv`):
- Total records: **72,134**
- Rows with `label == 0`: **35,028**
- Rows with `label == 1`: **37,106**

---

## 2. Analysis of the Conflict

- If statement 2 were taken as truth (`0 = fake, 1 = real`), then there would be **35,028 fake articles** and **37,106 real articles**. This contradicts statement 1's claim of 35,028 real articles.
- If statement 1 were taken as truth (**35,028 real articles**), then `0` corresponds to **real** (matching the count 35,028), making the legend statement 2 (`0 = fake`) a documentation typo.
- Furthermore, article content inspection shows that `Label 0` contains 21,643 wire-service Reuters news articles (matching the ISOT real-news benchmark dataset component of 21,417 articles), whereas `Label 1` contains blog posts, missing text fields, and clickbait articles.

---

## 3. Strict Preprocessing Policy Decision

Despite strong heuristic clues that `0 = real` and `1 = fake`:
- In accordance with dataset-quality guidelines and strict prompt rules, **we do NOT declare the mapping definitively resolved**.
- We preserve original raw labels (`0` and `1`) as `source_label`.
- Target `label` fields retain the string values `"0"` and `"1"`, with `label_status` explicitly set to `"unverified"`.
- Downstream machine learning training or evaluation MUST NOT present these labels as verified semantic ground truth until authoritative confirmation from the dataset authors is obtained.
