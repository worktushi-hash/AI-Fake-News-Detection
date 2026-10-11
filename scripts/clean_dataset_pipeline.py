"""Reproducible cleaning, deduplication, and quarantine pipeline.

Processes raw English (WELFake CSV), Hindi (.txt folder corpus), and Marathi
(.txt folder corpus) datasets without modifying any raw files.
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
    DATASETS_PROCESSED,
    DATASETS_QUARANTINE,
    DATASETS_RAW,
    REPORTS_DIR,
    infer_folder_label,
    is_macos_artifact,
    jaccard_similarity,
    minhash_signature,
    normalize_for_hash,
    read_text_file,
    script_stats,
    text_sha256,
    write_json,
    write_jsonl,
    write_text,
)


def process_english(csv_path: Path) -> dict[str, Any]:
    print(f"Processing English WELFake CSV from {csv_path}...")
    if not csv_path.is_file():
        raise FileNotFoundError(f"English CSV missing: {csv_path}")

    accepted_records = []
    quarantined_records = []
    excluded_records = []

    counts = Counter()
    hash_to_rows = defaultdict(list)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=1):
            counts["total_raw_rows"] += 1
            original_id = (row.get("") or "").strip() or str(row_idx)
            title = (row.get("title") or "").strip() or None
            text = (row.get("text") or "").strip()
            source_label = (row.get("label") or "").strip()

            if not text:
                counts["excluded_blank_text"] += 1
                excluded_records.append({
                    "language": "en",
                    "source_dataset": "WELFake",
                    "source_record_id": original_id,
                    "reason": "blank_text",
                    "details": "Text body is empty or whitespace-only",
                })
                continue

            clean_text = normalize_for_hash(text)
            digest = text_sha256(clean_text)

            hash_to_rows[digest].append({
                "source_record_id": original_id,
                "title": title,
                "text": clean_text,
                "source_label": source_label,
            })

    # Exact Deduplication & Conflict Check
    for digest, group in hash_to_rows.items():
        labels = sorted({r["source_label"] for r in group})
        if len(labels) > 1:
            # Conflicting labels across exact duplicates
            counts["quarantined_conflicting_labels"] += len(group)
            for r in group:
                quarantined_records.append({
                    "id": f"en_q{len(quarantined_records)+1:06d}",
                    "language": "en",
                    "title": r["title"],
                    "text": r["text"],
                    "source_dataset": "WELFake",
                    "source_record_id": r["source_record_id"],
                    "source_label": r["source_label"],
                    "label": r["source_label"],
                    "label_status": "unverified",
                    "review_status": "quarantined",
                    "quarantine_reason": "conflicting_labels",
                    "quarantine_details": f"Exact text appears with multiple raw labels: {labels}",
                })
        else:
            # Canonical record accepted; extras deduplicated
            canonical = group[0]
            rec_id = f"en_{len(accepted_records)+1:06d}"
            accepted_records.append({
                "id": rec_id,
                "language": "en",
                "title": canonical["title"],
                "text": canonical["text"],
                "label": canonical["source_label"],
                "source_dataset": "WELFake",
                "source_record_id": canonical["source_record_id"],
                "source_label": canonical["source_label"],
                "label_source": "WELFake_Dataset.csv",
                "label_status": "unverified",
                "review_status": "accepted",
            })
            counts["accepted_records"] += 1

            if len(group) > 1:
                counts["exact_duplicate_groups"] += 1
                counts["extra_duplicate_copies_excluded"] += len(group) - 1
                for extra in group[1:]:
                    excluded_records.append({
                        "language": "en",
                        "source_dataset": "WELFake",
                        "source_record_id": extra["source_record_id"],
                        "reason": "exact_duplicate",
                        "details": f"Exact text copy of canonical record {rec_id} (hash {digest[:12]})",
                    })

    out_file = DATASETS_PROCESSED / "english" / "english_clean.jsonl"
    write_jsonl(out_file, accepted_records)
    print(f"  English: Raw={counts['total_raw_rows']}, Accepted={len(accepted_records)}, Quarantined={len(quarantined_records)}, Excluded={len(excluded_records)}")

    return {
        "language": "english",
        "counts": dict(counts),
        "accepted_file": str(out_file),
        "quarantined": quarantined_records,
        "excluded": excluded_records,
    }


def process_txt_corpus(language: str, lang_dir: Path) -> dict[str, Any]:
    print(f"Processing {language.title()} txt corpus from {lang_dir}...")
    if not lang_dir.is_dir():
        raise FileNotFoundError(f"{language} folder missing: {lang_dir}")

    accepted_records = []
    quarantined_records = []
    excluded_records = []

    counts = Counter()
    hash_to_records = defaultdict(list)

    lang_prefix = "hi" if language == "hindi" else "mr"

    for path in lang_dir.rglob("*"):
        if not path.is_file():
            continue
        rel_path = str(path.relative_to(lang_dir)).replace("\\", "/")

        if is_macos_artifact(path):
            counts["excluded_os_artifacts"] += 1
            excluded_records.append({
                "language": lang_prefix,
                "source_dataset": f"{language.title()}_corpus",
                "source_record_id": rel_path,
                "reason": "os_artifact",
                "details": "Unzip leftover or macOS filesystem artifact",
            })
            continue

        if path.suffix.lower() != ".txt":
            counts["excluded_non_txt"] += 1
            excluded_records.append({
                "language": lang_prefix,
                "source_dataset": f"{language.title()}_corpus",
                "source_record_id": rel_path,
                "reason": "non_txt",
                "details": f"File extension {path.suffix} is not .txt",
            })
            continue

        counts["total_txt_files"] += 1
        folder_label = infer_folder_label(path)

        text, encoding, replaced = read_text_file(path)
        clean_text = normalize_for_hash(text)

        if not clean_text:
            counts["excluded_blank_text"] += 1
            excluded_records.append({
                "language": lang_prefix,
                "source_dataset": f"{language.title()}_corpus",
                "source_record_id": rel_path,
                "reason": "blank_text",
                "details": "File content is empty or whitespace-only",
            })
            continue

        stats = script_stats(clean_text)
        if stats["letter_chars"] >= 20 and stats["devanagari_ratio"] < 0.5:
            counts["quarantined_script_mismatch"] += 1
            quarantined_records.append({
                "id": f"{lang_prefix}_q{len(quarantined_records)+1:06d}",
                "language": lang_prefix,
                "title": None,
                "text": clean_text,
                "source_dataset": f"{language.title()}_corpus",
                "source_record_id": rel_path,
                "source_label": folder_label,
                "label": folder_label,
                "label_status": "claimed_folder_label",
                "review_status": "quarantined",
                "quarantine_reason": "script_mismatch",
                "quarantine_details": f"Devanagari character ratio is low ({stats['devanagari_ratio']:.2f})",
            })
            continue

        digest = text_sha256(clean_text)
        hash_to_records[digest].append({
            "source_record_id": rel_path,
            "text": clean_text,
            "folder_label": folder_label,
        })

    # Deduplication & Conflicting Label Quarantine
    for digest, group in hash_to_records.items():
        labels = sorted({r["folder_label"] for r in group})
        if len(labels) > 1:
            # Conflicting folder labels for exact text (e.g. fake AND real)
            counts["quarantined_conflicting_labels"] += len(group)
            for r in group:
                quarantined_records.append({
                    "id": f"{lang_prefix}_q{len(quarantined_records)+1:06d}",
                    "language": lang_prefix,
                    "title": None,
                    "text": r["text"],
                    "source_dataset": f"{language.title()}_corpus",
                    "source_record_id": r["source_record_id"],
                    "source_label": r["folder_label"],
                    "label": r["folder_label"],
                    "label_status": "claimed_folder_label",
                    "review_status": "quarantined",
                    "quarantine_reason": "conflicting_labels",
                    "quarantine_details": f"Exact text appears in multiple folder labels: {labels}",
                })
        else:
            # Accept 1 canonical record; log extra copies
            canonical = group[0]
            rec_id = f"{lang_prefix}_{len(accepted_records)+1:06d}"
            accepted_records.append({
                "id": rec_id,
                "language": lang_prefix,
                "title": None,
                "text": canonical["text"],
                "label": canonical["folder_label"],
                "source_dataset": f"{language.title()}_corpus",
                "source_record_id": canonical["source_record_id"],
                "source_label": canonical["folder_label"],
                "label_source": "folder_name",
                "label_status": "claimed_folder_label",
                "review_status": "accepted",
            })
            counts["accepted_records"] += 1

            if len(group) > 1:
                counts["exact_duplicate_groups"] += 1
                counts["extra_duplicate_copies_excluded"] += len(group) - 1
                for extra in group[1:]:
                    excluded_records.append({
                        "language": lang_prefix,
                        "source_dataset": f"{language.title()}_corpus",
                        "source_record_id": extra["source_record_id"],
                        "reason": "exact_duplicate",
                        "details": f"Exact text copy of canonical record {rec_id} (hash {digest[:12]})",
                    })

    out_file = DATASETS_PROCESSED / language / f"{language}_clean.jsonl"
    write_jsonl(out_file, accepted_records)
    print(f"  {language.title()}: Files={counts['total_txt_files']}, Accepted={len(accepted_records)}, Quarantined={len(quarantined_records)}, Excluded={len(excluded_records)}")

    return {
        "language": language,
        "counts": dict(counts),
        "accepted_file": str(out_file),
        "quarantined": quarantined_records,
        "excluded": excluded_records,
    }


def analyze_near_duplicates(accepted_by_lang: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    print("Performing MinHash near-duplicate analysis...")
    near_dup_report = {}

    for lang, records in accepted_by_lang.items():
        print(f"  MinHash indexing {len(records)} records for {lang}...")
        # To run efficiently in standard library, sample signatures and check length bucket candidates
        sample_size = min(len(records), 2000)
        sample = records[:sample_size]

        sigs = [minhash_signature(r["text"]) for r in sample]
        near_dup_pairs = []

        for i in range(len(sample)):
            for j in range(i + 1, min(i + 50, len(sample))):  # Banded candidate check
                sim = jaccard_similarity(sigs[i], sigs[j])
                if sim >= 0.85 and sample[i]["text"] != sample[j]["text"]:
                    near_dup_pairs.append({
                        "id1": sample[i]["id"],
                        "id2": sample[j]["id"],
                        "jaccard": round(sim, 3),
                        "text1_preview": sample[i]["text"][:100],
                        "text2_preview": sample[j]["text"][:100],
                    })

        near_dup_report[lang] = {
            "sample_records_analyzed": sample_size,
            "near_duplicate_pairs_found": len(near_dup_pairs),
            "threshold": 0.85,
            "sample_pairs": near_dup_pairs[:10],
        }

    return near_dup_report


def main() -> int:
    print("Starting dataset cleaning & quarantine pipeline...")

    # Process datasets
    en_res = process_english(DATASETS_RAW / "english" / "WELFake_Dataset.csv")
    hi_res = process_txt_corpus("hindi", DATASETS_RAW / "hindi")
    mr_res = process_txt_corpus("marathi", DATASETS_RAW / "marathi")

    # Combine quarantined records
    all_quarantined = en_res["quarantined"] + hi_res["quarantined"] + mr_res["quarantined"]
    quarantine_file = DATASETS_QUARANTINE / "quarantined_records.jsonl"
    write_jsonl(quarantine_file, all_quarantined)
    print(f"Wrote {len(all_quarantined)} quarantined records to {quarantine_file}")

    # Combine excluded summary
    all_excluded = en_res["excluded"] + hi_res["excluded"] + mr_res["excluded"]

    summary = {
        "english": en_res["counts"],
        "hindi": hi_res["counts"],
        "marathi": mr_res["counts"],
        "total_quarantined": len(all_quarantined),
        "total_excluded": len(all_excluded),
    }

    write_json(REPORTS_DIR / "pipeline_run_summary.json", summary)

    # Render exclusion & quarantine markdown report
    eq_lines = [
        "# Exclusion and Quarantine Summary Report",
        "",
        "This report details all records removed or quarantined during pipeline execution.",
        "",
        f"- Total Quarantined Records: **{len(all_quarantined)}**",
        f"- Total Excluded Records: **{len(all_excluded)}**",
        "",
        "## Quarantined Records Breakdown",
        "",
        "| ID | Language | Dataset | Source Record ID | Reason | Details |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for q in all_quarantined[:20]:
        eq_lines.append(f"| `{q['id']}` | `{q['language']}` | `{q['source_dataset']}` | `{q['source_record_id']}` | `{q['quarantine_reason']}` | {q['quarantine_details']} |")

    eq_lines.extend([
        "",
        "## Exclusion Summary by Reason Code",
        "",
        "| Language | Reason | Record Count | Description |",
        "| :--- | :--- | :--- | :--- |",
        f"| English | `blank_text` | {en_res['counts'].get('excluded_blank_text', 0)} | Blank or whitespace-only article body |",
        f"| English | `exact_duplicate` | {en_res['counts'].get('extra_duplicate_copies_excluded', 0)} | Redundant copy of exact text |",
        f"| Hindi | `os_artifact` | {hi_res['counts'].get('excluded_os_artifacts', 0)} | macOS `__MACOSX` or `._*` artifact |",
        f"| Hindi | `exact_duplicate` | {hi_res['counts'].get('extra_duplicate_copies_excluded', 0)} | Redundant copy of exact text |",
        f"| Marathi | `os_artifact` | {mr_res['counts'].get('excluded_os_artifacts', 0)} | macOS `__MACOSX` or `._*` artifact |",
        f"| Marathi | `exact_duplicate` | {mr_res['counts'].get('extra_duplicate_copies_excluded', 0)} | Redundant copy of exact text |",
        "",
    ])

    write_text(REPORTS_DIR / "exclusion_quarantine_summary.md", "\n".join(eq_lines))

    print("Pipeline execution complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
