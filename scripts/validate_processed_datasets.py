"""Automated validation runner for processed JSONL datasets."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fnd_common import (
    DATASETS_PROCESSED,
    DATASETS_QUARANTINE,
    DATASETS_RAW,
    REPORTS_DIR,
    file_sha256,
    read_jsonl,
    text_sha256,
    write_json,
    write_text,
)


def validate_jsonl_dataset(path: Path, expected_lang: str) -> dict[str, Any]:
    print(f"Validating dataset {path.name}...")
    if not path.is_file():
        raise FileNotFoundError(f"Processed dataset missing: {path}")

    seen_ids = set()
    seen_hashes = set()

    record_count = 0
    empty_texts = 0
    invalid_langs = 0
    invalid_labels = 0
    duplicate_ids = 0
    duplicate_texts = 0

    required_keys = {
        "id",
        "language",
        "title",
        "text",
        "label",
        "source_dataset",
        "source_record_id",
        "source_label",
        "label_source",
        "label_status",
        "review_status",
    }

    schema_violations = 0

    for rec in read_jsonl(path):
        record_count += 1
        keys = set(rec.keys())
        if not required_keys.issubset(keys):
            schema_violations += 1

        rec_id = rec.get("id")
        if rec_id in seen_ids:
            duplicate_ids += 1
        seen_ids.add(rec_id)

        lang = rec.get("language")
        if lang != expected_lang:
            invalid_langs += 1

        text = rec.get("text") or ""
        if not text.strip():
            empty_texts += 1

        digest = text_sha256(text)
        if digest in seen_hashes:
            duplicate_texts += 1
        seen_hashes.add(digest)

        label = str(rec.get("label") or "")
        if not label:
            invalid_labels += 1

    validation_result = {
        "file": str(path.relative_to(path.parent.parent.parent)),
        "record_count": record_count,
        "unique_ids": len(seen_ids),
        "unique_texts": len(seen_hashes),
        "schema_violations": schema_violations,
        "duplicate_ids": duplicate_ids,
        "duplicate_texts": duplicate_texts,
        "empty_texts": empty_texts,
        "invalid_languages": invalid_langs,
        "invalid_labels": invalid_labels,
        "passed": (
            schema_violations == 0
            and duplicate_ids == 0
            and duplicate_texts == 0
            and empty_texts == 0
            and invalid_langs == 0
            and invalid_labels == 0
        ),
    }

    return validation_result


def main() -> int:
    print("Running dataset validation suite...")
    results = []

    en_file = DATASETS_PROCESSED / "english" / "english_clean.jsonl"
    hi_file = DATASETS_PROCESSED / "hindi" / "hindi_clean.jsonl"
    mr_file = DATASETS_PROCESSED / "marathi" / "marathi_clean.jsonl"

    res_en = validate_jsonl_dataset(en_file, "en")
    res_hi = validate_jsonl_dataset(hi_file, "hi")
    res_mr = validate_jsonl_dataset(mr_file, "mr")

    results.extend([res_en, res_hi, res_mr])

    all_passed = all(r["passed"] for r in results)

    report_payload = {
        "validation_passed": all_passed,
        "datasets": results,
    }

    write_json(REPORTS_DIR / "validation_results.json", report_payload)

    val_lines = [
        "# Dataset Validation Results",
        "",
        f"- Overall Status: **{'PASSED' if all_passed else 'FAILED'}**",
        "",
        "## Detailed Checks",
        "",
        "| Dataset File | Record Count | Unique IDs | Unique Texts | Schema Violations | Duplicate Texts | Empty Texts | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in results:
        status = "PASSED" if r["passed"] else "FAILED"
        val_lines.append(
            f"| `{r['file']}` | {r['record_count']:,} | {r['unique_ids']:,} | {r['unique_texts']:,} | {r['schema_violations']} | {r['duplicate_texts']} | {r['empty_texts']} | **{status}** |"
        )

    val_lines.append("")
    write_text(REPORTS_DIR / "validation_results.md", "\n".join(val_lines))

    print(f"Validation complete. Overall Passed: {all_passed}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
