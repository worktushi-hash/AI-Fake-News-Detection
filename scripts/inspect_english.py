"""Read-only audit of the local WELFake English CSV.

This script does not interpret label 0/1 as fake or real. See
reports/welfake_label_mapping.md for the documentation conflict.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

csv.field_size_limit(2147483647)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fnd_common import (
    DATASETS_RAW,
    REPORTS_DIR,
    script_stats,
    text_sha256,
    write_json,
    write_text,
)

DEFAULT_CSV = DATASETS_RAW / "english" / "WELFake_Dataset.csv"
MAX_EXAMPLES = 5
SHORT_CHAR_THRESHOLD = 50


def audit_english_csv(path: Path, sample_limit: int = MAX_EXAMPLES) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {path}")

    label_counts: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    invalid_labels: Counter[str] = Counter()
    samples: dict[str, list[dict[str, str]]] = {"0": [], "1": []}
    hash_to_rows: dict[str, list[dict[str, str]]] = defaultdict(list)

    row_count = 0
    short_text = 0
    latin_heavy = 0
    url_rows = 0
    unnamed_index_present = False

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = list(reader.fieldnames or [])
        unnamed_index_present = any(name == "" or name is None for name in fieldnames)

        required_columns = {"title", "text", "label"}
        if not required_columns.issubset(set(fieldnames)):
            raise ValueError(
                f"Expected columns {required_columns}, but found {fieldnames}"
            )

        for row_number, row in enumerate(reader, start=1):
            row_count += 1
            title = (row.get("title") or "").strip()
            text = (row.get("text") or "").strip()
            label = (row.get("label") or "").strip()
            original_id = (row.get("") or "").strip() or str(row_number)

            if not title:
                missing["title"] += 1
            if not text:
                missing["text"] += 1
            if not label:
                missing["label"] += 1

            label_counts[label] += 1
            if label not in ("0", "1"):
                invalid_labels[label] += 1

            if label in samples and len(samples[label]) < sample_limit:
                samples[label].append(
                    {
                        "original_id": original_id,
                        "title": title[:150],
                        "text": text[:250],
                        "label": label,
                    }
                )

            if text and len(text) < SHORT_CHAR_THRESHOLD:
                short_text += 1

            if text:
                stats = script_stats(text)
                if stats["contains_url"]:
                    url_rows += 1
                if stats["letter_chars"] >= 20 and stats["latin_ratio"] >= 0.8:
                    latin_heavy += 1
                digest = text_sha256(text)
                hash_to_rows[digest].append(
                    {
                        "original_id": original_id,
                        "label": label,
                    }
                )

    duplicate_groups = []
    conflicting_groups = []
    extra_duplicate_copies = 0
    for digest, records in hash_to_rows.items():
        if len(records) < 2:
            continue
        extra_duplicate_copies += len(records) - 1
        labels = sorted({item["label"] for item in records})
        group = {
            "sha256": digest,
            "count": len(records),
            "labels": labels,
            "original_ids": [item["original_id"] for item in records[:10]],
        }
        duplicate_groups.append(group)
        if len(labels) > 1:
            conflicting_groups.append(group)

    duplicate_groups.sort(key=lambda item: item["count"], reverse=True)
    conflicting_groups.sort(key=lambda item: item["count"], reverse=True)

    return {
        "language": "english",
        "dataset": "WELFake",
        "csv_path": str(path),
        "raw_files_modified": False,
        "columns": fieldnames,
        "unnamed_index_column_present": unnamed_index_present,
        "parsed_records": row_count,
        "label_counts": dict(label_counts),
        "missing_or_blank": {
            "title": missing["title"],
            "text": missing["text"],
            "label": missing["label"],
        },
        "unexpected_labels": dict(invalid_labels),
        "short_text_under_chars": {
            "threshold": SHORT_CHAR_THRESHOLD,
            "count": short_text,
        },
        "rows_containing_url": url_rows,
        "latin_heavy_rows": latin_heavy,
        "unique_normalized_texts": len(hash_to_rows),
        "duplicate_groups": len(duplicate_groups),
        "extra_duplicate_copies": extra_duplicate_copies,
        "conflicting_label_groups": len(conflicting_groups),
        "label_mapping_status": "unverified",
        "label_mapping_note": (
            "Do not treat 0/1 as fake/real until reports/welfake_label_mapping.md "
            "is confirmed by a human. Published counts and the 0/1 legend disagree."
        ),
        "samples": samples,
        "examples": {
            "largest_duplicate_groups": duplicate_groups[:10],
            "conflicting_label_groups": conflicting_groups[:10],
        },
    }


def print_console_report(report: dict[str, Any]) -> None:
    print("Columns:", report["columns"])
    print("\nParsed records:", report["parsed_records"])
    print("\nLabel counts:")
    for label, count in sorted(report["label_counts"].items()):
        print(f"  {label!r}: {count}")
    print("\nMissing or blank fields:")
    for column, count in report["missing_or_blank"].items():
        print(f"  {column}: {count}")
    print("\nUnexpected labels:", report["unexpected_labels"])
    print("\nExact-text duplicate groups:", report["duplicate_groups"])
    print("Extra duplicate copies:", report["extra_duplicate_copies"])
    print("Same text, different labels:", report["conflicting_label_groups"])
    print("\nLabel mapping status:", report["label_mapping_status"])
    print(report["label_mapping_note"])
    for label in ("0", "1"):
        print(f"\n--- Samples with label {label} ---")
        for item in report["samples"].get(label, []):
            print("\nTitle:", item["title"])
            print("Text:", item["text"])
            print("Label:", item["label"])
    print("\nAudit complete. The original CSV was not modified.")


def render_markdown(report: dict[str, Any]) -> str:
    labels = report["label_counts"]
    lines = [
        "# English WELFake audit",
        "",
        "Raw files were not modified. Labels `0` and `1` are reported as stored.",
        "",
        f"- Parsed records: **{report['parsed_records']}**",
        f"- Label `0`: **{labels.get('0', 0)}**",
        f"- Label `1`: **{labels.get('1', 0)}**",
        f"- Blank titles: **{report['missing_or_blank']['title']}**",
        f"- Blank texts: **{report['missing_or_blank']['text']}**",
        f"- Unexpected labels: **{report['unexpected_labels'] or 'none'}**",
        f"- Unique normalized texts: **{report['unique_normalized_texts']}**",
        f"- Duplicate groups: **{report['duplicate_groups']}**",
        f"- Extra duplicate copies: **{report['extra_duplicate_copies']}**",
        f"- Same text, different labels: **{report['conflicting_label_groups']}**",
        "",
        f"**Label mapping status:** {report['label_mapping_status']}",
        "",
        report["label_mapping_note"],
        "",
        "See `reports/welfake_label_mapping.md`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    path = DEFAULT_CSV
    print("CSV path:", path)
    print("File exists:", path.is_file())
    report = audit_english_csv(path)
    json_path = REPORTS_DIR / "audit_english.json"
    md_path = REPORTS_DIR / "audit_english.md"
    # Keep article bodies out of the JSON report.
    serializable = dict(report)
    serializable["samples"] = {
        label: [
            {
                "original_id": item["original_id"],
                "title_chars": len(item["title"]),
                "text_chars": len(item["text"]),
                "label": item["label"],
            }
            for item in items
        ]
        for label, items in report["samples"].items()
    }
    write_json(json_path, serializable)
    write_text(md_path, render_markdown(report))
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    try:
        print_console_report(report)
    except UnicodeEncodeError:
        print(
            "Console cannot print some sample characters on this Windows "
            "code page. The JSON/Markdown reports were still written."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
