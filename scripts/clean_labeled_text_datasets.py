"""Clean, deduplicate, and audit the LIAR and Marathi-headline datasets.

These two datasets do NOT use the binary Fake/Real schema of the main pipeline:

* LIAR: short English political statements with six original truthfulness
  labels (pants-fire ... true) and official train/valid/test splits.
* Marathi headlines: Devanagari headlines labelled with news *topic* categories
  (state / entertainment / sports), with train/valid splits.

Policy (mirrors clean_dataset_pipeline.py where applicable):

* Raw files are never modified; SHA-256 hashes are taken before and after.
* Original text and original labels are preserved verbatim. Normalization
  (NFC + whitespace collapse, via fnd_common.normalize_for_hash) is used ONLY
  as a comparison key.
* Missing / whitespace-only text and malformed rows are excluded and logged.
* Within one split: exact-duplicate copies with the same label keep the first
  record and exclude the extras (logged); copies with conflicting labels are
  quarantined (all copies), as in the main pipeline.
* Across splits: duplicates are REPORTED as potential leakage and flagged on
  the records. Nothing is moved or deleted and official splits are untouched.
* No approximate/near-duplicate removal is performed.
* No binary Fake/Real labels are created. Any such mapping must be a separate,
  explicitly approved step.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

csv.field_size_limit(2147483647)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fnd_common import (  # noqa: E402
    DATASETS_PROCESSED,
    DATASETS_QUARANTINE,
    DATASETS_RAW,
    REPORTS_DIR,
    file_sha256,
    normalize_for_hash,
    read_jsonl,
    script_stats,
    text_sha256,
    write_json,
    write_jsonl,
)

LIAR_LABELS = ("pants-fire", "false", "barely-true", "half-true", "mostly-true", "true")
LIAR_SPLIT_FILES = {"train": "train.tsv", "valid": "valid.tsv", "test": "test.tsv"}
LIAR_COLUMNS = (
    "statement_id", "label", "statement", "subjects", "speaker", "speaker_job",
    "state", "party", "barely_true_count", "false_count", "half_true_count",
    "mostly_true_count", "pants_fire_count", "context",
)
MARATHI_SPLIT_FILES = {"train": "train.csv", "valid": "valid.csv"}
NORMALIZATION_METHOD = (
    "fnd_common.normalize_for_hash: whitespace collapsed to single spaces, then "
    "Unicode NFC; SHA-256 of the UTF-8 result is the duplicate key. Original "
    "text is stored unchanged in `text`; case, punctuation and diacritics are kept."
)
EXISTING_PROCESSED = {
    "english": "english_clean.jsonl",
    "hindi": "hindi_clean.jsonl",
    "marathi": "marathi_clean.jsonl",
}


# --------------------------------------------------------------------------- #
# Readers (return raw rows; never raise on a single bad row)
# --------------------------------------------------------------------------- #
def read_liar_rows(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Return (rows, malformed, columns). TSV has no header; 14 columns per README."""
    rows: list[dict[str, Any]] = []
    malformed: list[dict[str, Any]] = []
    # newline="" + csv with QUOTE_NONE: the raw TSV contains literal quote characters.
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for line_no, parts in enumerate(reader, start=1):
            if not parts:
                malformed.append({"line": line_no, "problem": "blank_line"})
                continue
            if len(parts) != len(LIAR_COLUMNS):
                malformed.append({
                    "line": line_no,
                    "problem": f"expected {len(LIAR_COLUMNS)} columns, got {len(parts)}",
                })
                continue
            row = dict(zip(LIAR_COLUMNS, parts))
            row["_line"] = line_no
            rows.append(row)
    return rows, malformed, list(LIAR_COLUMNS)


def read_marathi_rows(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    malformed: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        if not {"headline", "label"}.issubset(columns):
            raise ValueError(f"{path.name}: expected columns headline,label; found {columns}")
        for line_no, row in enumerate(reader, start=2):  # header is line 1
            if None in row or any(v is None for v in row.values()):
                malformed.append({"line": line_no, "problem": "wrong_field_count"})
                continue
            row["_line"] = line_no
            rows.append(row)
    return rows, malformed, columns


# --------------------------------------------------------------------------- #
# Core, dataset-agnostic cleaning
# --------------------------------------------------------------------------- #
def clean_dataset(
    *,
    dataset_key: str,
    id_prefix: str,
    language: str,
    source_dataset: str,
    split_rows: dict[str, list[dict[str, Any]]],
    text_field: str,
    label_field: str,
    valid_labels: tuple[str, ...] | None,
    label_scheme: str,
    task: str,
    label_status: str,
    label_source_by_split: dict[str, str],
    id_field: str | None,
    metadata_fields: tuple[str, ...],
    script_check: bool,
) -> dict[str, Any]:
    """Apply the shared policy. Returns accepted/excluded/quarantined + stats."""
    stats: dict[str, Any] = {
        "per_split": {},
        "invalid_label_counts": Counter(),
        "invalid_label_examples": [],
    }
    excluded: list[dict[str, Any]] = []
    candidates: dict[str, list[dict[str, Any]]] = {s: [] for s in split_rows}

    for split, rows in split_rows.items():
        sp = Counter()
        sp["records_read"] = len(rows)
        for row in rows:
            text_raw = row.get(text_field) or ""
            label = (row.get(label_field) or "").strip()
            src_id = (row.get(id_field) or "").strip() if id_field else ""
            src_id = src_id or f"{split}:line{row['_line']}"

            if not text_raw.strip():
                sp["excluded_missing_text"] += 1
                excluded.append(_exclusion(split, src_id, "missing_text",
                                           "Text is empty or whitespace-only", label))
                continue
            if not label or (valid_labels is not None and label not in valid_labels):
                sp["excluded_invalid_label"] += 1
                stats["invalid_label_counts"][label or "<empty>"] += 1
                if len(stats["invalid_label_examples"]) < 10:
                    stats["invalid_label_examples"].append(
                        {"split": split, "source_record_id": src_id, "label": label})
                excluded.append(_exclusion(split, src_id, "invalid_label",
                                           f"Label {label!r} is empty or not in the allowed set", label))
                continue
            if script_check:
                st = script_stats(normalize_for_hash(text_raw))
                if st["letter_chars"] > 0 and st["devanagari_chars"] == 0:
                    sp["excluded_no_devanagari"] += 1
                    excluded.append(_exclusion(split, src_id, "no_devanagari",
                                               "Text contains letters but no Devanagari characters", label))
                    continue
                if st["letter_chars"] > 0 and st["devanagari_ratio"] < 0.5:
                    sp["warning_low_devanagari_ratio_retained"] += 1

            candidates[split].append({
                "split": split,
                "source_record_id": src_id,
                "text": text_raw.strip(),  # only outer whitespace trimmed; inner text untouched
                "label": label,
                "digest": text_sha256(text_raw),
                "metadata": {k: row.get(k) for k in metadata_fields} if metadata_fields else None,
            })
        stats["per_split"][split] = sp

    # ---- within-split exact duplicates -------------------------------------
    accepted: dict[str, list[dict[str, Any]]] = {s: [] for s in split_rows}
    quarantined: list[dict[str, Any]] = []
    duplicate_groups: list[dict[str, Any]] = []
    counter = 0

    for split, cands in candidates.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for c in cands:
            groups[c["digest"]].append(c)
        sp = stats["per_split"][split]
        for digest, grp in groups.items():
            labels = sorted({g["label"] for g in grp})
            if len(grp) > 1:
                sp["within_split_duplicate_groups"] += 1
                sp["within_split_duplicate_records"] += len(grp)
            if len(grp) > 1 and len(labels) > 1:
                sp["quarantined_conflicting_labels"] += len(grp)
                sp["within_split_conflicting_label_groups"] += 1
                for g in grp:
                    quarantined.append({
                        **_base_record(g, None, id_prefix, language, source_dataset, label_scheme,
                                       task, label_status, label_source_by_split),
                        "review_status": "quarantined",
                        "quarantine_reason": "conflicting_labels_within_split",
                        "quarantine_details": f"Exact normalized text appears with labels {labels}",
                    })
                duplicate_groups.append(_group_entry(split, digest, grp, "quarantined_conflicting_labels"))
                continue
            canonical = grp[0]
            counter += 1
            rec_id = f"{id_prefix}_{counter:06d}"
            accepted[split].append({"_cand": canonical, "id": rec_id, "digest": digest})
            if len(grp) > 1:
                duplicate_groups.append(_group_entry(split, digest, grp, "kept_first_excluded_extras"))
                for extra in grp[1:]:
                    sp["excluded_exact_duplicate"] += 1
                    excluded.append(_exclusion(
                        split, extra["source_record_id"], "exact_duplicate",
                        f"Exact normalized-text copy of retained record {rec_id} (hash {digest[:12]})",
                        extra["label"]))
        sp["records_retained"] = len(accepted[split])

    # ---- cross-split duplicates (report + flag, never move) -----------------
    digest_to_splits: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    digest_labels: dict[str, set[str]] = defaultdict(set)
    for split, cands in candidates.items():
        for c in cands:
            digest_to_splits[c["digest"]][split].append(c["source_record_id"])
            digest_labels[c["digest"]].add(c["label"])
    cross: dict[str, Any] = {"pairs": {}, "groups_total": 0, "conflicting_label_groups": 0,
                             "examples": []}
    cross_digests = {d for d, s in digest_to_splits.items() if len(s) > 1}
    cross["groups_total"] = len(cross_digests)
    for d in cross_digests:
        spl = sorted(digest_to_splits[d])
        for i in range(len(spl)):
            for j in range(i + 1, len(spl)):
                key = f"{spl[i]}__{spl[j]}"
                cross["pairs"][key] = cross["pairs"].get(key, 0) + 1
        if len(digest_labels[d]) > 1:
            cross["conflicting_label_groups"] += 1
        if len(cross["examples"]) < 20:
            cross["examples"].append({
                "hash_prefix": d[:12],
                "splits": {s: ids[:5] for s, ids in digest_to_splits[d].items()},
                "labels": sorted(digest_labels[d]),
            })

    final: dict[str, list[dict[str, Any]]] = {}
    for split, items in accepted.items():
        out = []
        for it in items:
            c = it["_cand"]
            rec = _base_record(c, it["id"], id_prefix, language, source_dataset, label_scheme,
                               task, label_status, label_source_by_split)
            rec["review_status"] = "accepted"
            rec["cross_split_duplicate"] = it["digest"] in cross_digests
            rec["cross_split_duplicate_splits"] = (
                sorted(s for s in digest_to_splits[it["digest"]] if s != split)
                if it["digest"] in cross_digests else [])
            out.append(rec)
        final[split] = out

    return {
        "accepted": final,
        "excluded": excluded,
        "quarantined": quarantined,
        "duplicate_groups": duplicate_groups,
        "cross_split": cross,
        "stats": stats,
        "cross_digests": cross_digests,
        "all_digests": {c["digest"] for cands in candidates.values() for c in cands},
    }


def resolve_cross_split_leakage(res: dict[str, Any]) -> dict[str, Any]:
    """Applies the documented leakage-resolution policy to produce zero-leakage splits.

    Rules:
    1. Same-label duplicates across train and evaluation (valid/test):
       Retain the evaluation copy in valid/test; exclude the train copy
       with reason `cross_split_duplicate_removed_from_train`.
    2. Conflicting-label duplicates across splits:
       Quarantine all copies with reason `cross_split_conflicting_label`.
    3. Evaluation cross-split duplicates (valid vs test):
       Retain valid copy; exclude test copy.
    """
    accepted = res["accepted"]
    cross_digests = res["cross_digests"]

    digest_records: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for split, recs in accepted.items():
        for r in recs:
            digest_records[r["text_sha256"]][split].append(r)

    accepted_no_leakage: dict[str, list[dict[str, Any]]] = {s: [] for s in accepted}
    excluded_no_leakage = list(res["excluded"])
    quarantined_no_leakage = list(res["quarantined"])
    resolution_log: list[dict[str, Any]] = []

    for split, recs in accepted.items():
        for r in recs:
            d = r["text_sha256"]
            if d not in cross_digests:
                accepted_no_leakage[split].append(r)
                continue

            splits_for_digest = digest_records[d]
            all_labels_for_digest = {rec["label"] for s_recs in splits_for_digest.values() for rec in s_recs}

            # Case A: Conflicting labels across splits
            if len(all_labels_for_digest) > 1:
                q_rec = dict(r)
                q_rec["review_status"] = "quarantined"
                q_rec["quarantine_reason"] = "cross_split_conflicting_label"
                q_rec["quarantine_details"] = (
                    f"Exact text appears across splits {sorted(splits_for_digest.keys())} "
                    f"with conflicting labels {sorted(all_labels_for_digest)}"
                )
                quarantined_no_leakage.append(q_rec)
                resolution_log.append({
                    "action": "quarantined_conflicting_label",
                    "split": split,
                    "record_id": r["id"],
                    "source_record_id": r["source_record_id"],
                    "text_sha256_prefix": d[:12],
                    "labels": sorted(all_labels_for_digest),
                })
            else:
                # Case B: Same label across splits
                has_eval_split = any(s in ("valid", "test") for s in splits_for_digest.keys() if s != split)
                if split == "train" and has_eval_split:
                    ex_entry = _exclusion(
                        split, r["source_record_id"], "cross_split_duplicate_removed_from_train",
                        f"Exact normalized text copy preserved in evaluation split(s) "
                        f"{sorted(s for s in splits_for_digest.keys() if s != 'train')}; removed from train to prevent evaluation leakage.",
                        r["label"]
                    )
                    excluded_no_leakage.append(ex_entry)
                    resolution_log.append({
                        "action": "excluded_from_train",
                        "split": split,
                        "record_id": r["id"],
                        "source_record_id": r["source_record_id"],
                        "text_sha256_prefix": d[:12],
                        "eval_splits": sorted(s for s in splits_for_digest.keys() if s != "train"),
                    })
                elif split == "test" and "valid" in splits_for_digest:
                    ex_entry = _exclusion(
                        split, r["source_record_id"], "cross_split_duplicate_removed_from_test",
                        "Exact normalized text copy preserved in valid split; removed from test.",
                        r["label"]
                    )
                    excluded_no_leakage.append(ex_entry)
                else:
                    clean_r = dict(r)
                    clean_r["cross_split_duplicate"] = False
                    clean_r["cross_split_duplicate_splits"] = []
                    accepted_no_leakage[split].append(clean_r)

    # Verification: verify 0 cross-split overlap remains in accepted_no_leakage
    no_leak_digests: dict[str, set[str]] = defaultdict(set)
    for s, recs in accepted_no_leakage.items():
        for r in recs:
            no_leak_digests[r["text_sha256"]].add(s)
    cross_overlap_count = sum(1 for s_set in no_leak_digests.values() if len(s_set) > 1)

    return {
        "accepted_no_leakage": accepted_no_leakage,
        "excluded_no_leakage": excluded_no_leakage,
        "quarantined_no_leakage": quarantined_no_leakage,
        "cross_split_groups_no_leakage": cross_overlap_count,
        "resolution_log": resolution_log,
        "verification_passed": (cross_overlap_count == 0),
    }


def _exclusion(split: str, src_id: str, reason: str, details: str, label: str) -> dict[str, Any]:
    return {"split": split, "source_record_id": src_id, "source_label": label,
            "reason": reason, "details": details}


def _group_entry(split: str, digest: str, grp: list[dict[str, Any]], action: str) -> dict[str, Any]:
    return {
        "split": split,
        "hash_prefix": digest[:12],
        "size": len(grp),
        "action": action,
        "source_record_ids": [g["source_record_id"] for g in grp],
        "labels": [g["label"] for g in grp],
        "text_preview": grp[0]["text"][:120],
    }


def _base_record(c, rec_id, id_prefix, language, source_dataset, label_scheme, task,
                 label_status, label_source_by_split) -> dict[str, Any]:
    rec = {
        "id": rec_id if rec_id else f"{id_prefix}_q_{c['split']}_{c['source_record_id']}",
        "language": language,
        "title": None,
        "text": c["text"],
        "label": c["label"],  # original label, never remapped
        "source_dataset": source_dataset,
        "source_record_id": c["source_record_id"],
        "source_label": c["label"],
        "label_source": label_source_by_split[c["split"]],
        "label_status": label_status,
        "review_status": None,
        "split": c["split"],
        "task": task,
        "label_scheme": label_scheme,
        "text_sha256": c["digest"],
    }
    if c.get("metadata") is not None:
        rec["metadata"] = c["metadata"]
    return rec


# --------------------------------------------------------------------------- #
# Dataset drivers
# --------------------------------------------------------------------------- #
def process_dataset(kind: str, raw_dir: Path, out_dir: Path, quarantine_dir: Path,
                    reports_dir: Path, processed_root: Path) -> dict[str, Any]:
    cfg = _CONFIG[kind]
    report: dict[str, Any] = {
        "dataset": cfg["name"], "task": cfg["task"], "raw_dir": str(raw_dir),
        "errors": [], "warnings": [], "input_files": {}, "detected_columns": {},
        "malformed_rows": {}, "text_normalization": NORMALIZATION_METHOD,
    }
    hashes_before: dict[str, str] = {}
    split_rows: dict[str, list[dict[str, Any]]] = {}
    malformed_full: dict[str, list[dict[str, Any]]] = {}

    for split, fname in cfg["files"].items():
        path = raw_dir / fname
        if not path.is_file():
            report["errors"].append(f"Missing input file: {path}")
            continue
        hashes_before[fname] = file_sha256(path)
        try:
            rows, malformed, cols = cfg["reader"](path)
        except (ValueError, UnicodeDecodeError, csv.Error) as exc:
            report["errors"].append(f"{fname}: {exc}")
            continue
        split_rows[split] = rows
        report["input_files"][fname] = {"split": split, "sha256": hashes_before[fname],
                                        "bytes": path.stat().st_size}
        report["detected_columns"][fname] = cols
        report["malformed_rows"][fname] = {"count": len(malformed), "examples": malformed[:10]}
        malformed_full[split] = malformed
        if not rows and not malformed:
            report["warnings"].append(f"{fname} contains no records")
        if malformed:
            report["warnings"].append(f"{fname}: {len(malformed)} malformed row(s) excluded")

    if not split_rows:
        report["status"] = "not_run_no_input"
        report["suitability"] = cfg["suitability"]
        _write_report(reports_dir / cfg["report"], report)
        return report

    res = clean_dataset(split_rows=split_rows, **cfg["clean_args"])
    # malformed rows are exclusions too (logged individually)
    for split, bad in malformed_full.items():
        res["stats"]["per_split"][split]["excluded_malformed"] = len(bad)
        res["stats"]["per_split"][split]["records_read"] += len(bad)
        for m in bad:
            res["excluded"].append(_exclusion(split, f"{split}:line{m['line']}", "malformed_row",
                                              m["problem"], ""))

    out_files = {}
    for split, recs in res["accepted"].items():
        p = out_dir / f"{cfg['prefix']}_{split}_clean.jsonl"
        write_jsonl(p, recs)
        out_files[split] = str(p)

    # Perform leakage resolution to generate zero-leakage training datasets
    leakage_res = resolve_cross_split_leakage(res)
    no_leakage_out_files = {}
    for split, recs in leakage_res["accepted_no_leakage"].items():
        p = out_dir / f"{cfg['prefix']}_{split}_no_leakage_clean.jsonl"
        write_jsonl(p, recs)
        no_leakage_out_files[split] = str(p)

    excl_path = out_dir / f"{cfg['prefix']}_excluded.jsonl"
    dup_path = out_dir / f"{cfg['prefix']}_duplicate_groups.jsonl"
    quar_path = quarantine_dir / f"{cfg['prefix']}_quarantined.jsonl"
    write_jsonl(excl_path, res["excluded"])
    write_jsonl(dup_path, res["duplicate_groups"])
    write_jsonl(quar_path, res["quarantined"])

    # label distribution (retained) and raw distribution
    label_dist = {s: dict(Counter(r["label"] for r in recs)) for s, recs in res["accepted"].items()}
    raw_dist = {s: dict(Counter((r.get(cfg["clean_args"]["label_field"]) or "").strip() for r in rows))
                for s, rows in split_rows.items()}

    per_split = {}
    for s, c in res["stats"]["per_split"].items():
        per_split[s] = dict(c)
    totals = Counter()
    for c in per_split.values():
        totals.update({k: v for k, v in c.items()})

    report.update({
        "status": "completed_with_errors" if report["errors"] else "completed",
        "total_records_read": totals["records_read"],
        "per_split": per_split,
        "totals": dict(totals),
        "missing_text_counts": {s: c.get("excluded_missing_text", 0) for s, c in per_split.items()},
        "label_distribution_raw": raw_dist,
        "label_distribution_retained": label_dist,
        "invalid_label_counts": dict(res["stats"]["invalid_label_counts"]),
        "invalid_label_examples": res["stats"]["invalid_label_examples"],
        "duplicates": {
            "within_split_groups": {s: c.get("within_split_duplicate_groups", 0) for s, c in per_split.items()},
            "within_split_records_in_groups": {s: c.get("within_split_duplicate_records", 0) for s, c in per_split.items()},
            "within_split_conflicting_label_groups": {s: c.get("within_split_conflicting_label_groups", 0) for s, c in per_split.items()},
            "exact_duplicate_records_excluded": {s: c.get("excluded_exact_duplicate", 0) for s, c in per_split.items()},
            "groups_example_file": str(dup_path),
            "cross_split": {
                "groups_total": res["cross_split"]["groups_total"],
                "pair_counts": res["cross_split"]["pairs"],
                "conflicting_label_groups": res["cross_split"]["conflicting_label_groups"],
                "examples": res["cross_split"]["examples"],
                "note": "Potential train/eval leakage in official benchmark splits. "
                        "Flagged with cross_split_duplicate=true in *_clean.jsonl, "
                        "and resolved completely in *_no_leakage_clean.jsonl.",
            },
            "near_duplicate_analysis": "not performed; no approximate-similarity removal is applied",
        },
        "leakage_resolution": {
            "policy": (
                "1. Official benchmark splits are preserved in *_clean.jsonl with cross_split_duplicate=true flag.\n"
                "2. Zero-leakage training datasets (*_no_leakage_clean.jsonl) are generated where:\n"
                "   - Conflicting cross-split labels are quarantined.\n"
                "   - Same-label duplicates matching evaluation splits are excluded from train."
            ),
            "cross_split_groups_before": res["cross_split"]["groups_total"],
            "cross_split_groups_after": leakage_res["cross_split_groups_no_leakage"],
            "verification_passed": leakage_res["verification_passed"],
            "actions_taken": len(leakage_res["resolution_log"]),
            "resolution_log": leakage_res["resolution_log"],
            "no_leakage_outputs": no_leakage_out_files,
        },

        "records_retained": sum(len(v) for v in res["accepted"].values()),
        "records_excluded": len(res["excluded"]),
        "records_quarantined": len(res["quarantined"]),
        "accounting_balanced": (
            totals["records_read"]
            == sum(len(v) for v in res["accepted"].values()) + len(res["excluded"]) + len(res["quarantined"])
        ),
        "exclusion_reasons": dict(Counter(e["reason"] for e in res["excluded"])),
        "cross_dataset_duplicates": _cross_dataset_check(res["all_digests"], processed_root),
        "outputs": {"clean_by_split": out_files, "excluded": str(excl_path),
                    "duplicate_groups": str(dup_path), "quarantine": str(quar_path),
                    "report": str(reports_dir / cfg["report"])},
        "suitability": cfg["suitability"],
        "limitations": cfg["limitations"],
    })

    # integrity: re-hash inputs after processing
    modified = [f for f, h in hashes_before.items() if file_sha256(raw_dir / f) != h]
    report["raw_files_modified"] = bool(modified)
    if modified:
        report["errors"].append(f"RAW FILES CHANGED DURING RUN: {modified}")

    if not report["accounting_balanced"]:
        report["errors"].append("Record accounting mismatch: read != retained + excluded + quarantined")
    report["validation"] = validate_outputs(kind, out_files, cfg)
    if not report["validation"]["passed"]:
        report["errors"].append("Output validation failed; see `validation`.")
    _write_report(reports_dir / cfg["report"], report)
    print(f"  {cfg['name']}: read={report['total_records_read']} retained={report['records_retained']} "
          f"excluded={report['records_excluded']} quarantined={report['records_quarantined']} "
          f"cross_split_groups={res['cross_split']['groups_total']}")
    return report


def _cross_dataset_check(digests: set[str], processed_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, fname in EXISTING_PROCESSED.items():
        p = processed_root / name / fname
        if not p.is_file():
            out[name] = {"status": "not_available_locally", "path": str(p)}
            continue
        hits = 0
        total = 0
        for rec in read_jsonl(p):
            total += 1
            if text_sha256(rec.get("text") or "") in digests:
                hits += 1
        out[name] = {"status": "checked", "existing_records_compared": total,
                     "exact_matches": hits}
    return out


def validate_outputs(kind: str, out_files: dict[str, str], cfg: dict[str, Any]) -> dict[str, Any]:
    """Validate the dataset-specific schema (superset of the main pipeline's keys)."""
    required = {"id", "language", "title", "text", "label", "source_dataset", "source_record_id",
                "source_label", "label_source", "label_status", "review_status", "split",
                "task", "label_scheme", "text_sha256", "cross_split_duplicate"}
    valid_labels = cfg["clean_args"]["valid_labels"]
    problems: Counter = Counter()
    seen_ids: set[str] = set()
    per_split_hashes: dict[str, set[str]] = {}
    counts: dict[str, int] = {}
    for split, path in out_files.items():
        hashes = per_split_hashes.setdefault(split, set())
        counts[split] = 0
        for rec in read_jsonl(Path(path)):
            counts[split] += 1
            if not required.issubset(rec):
                problems["schema_violations"] += 1
            if rec["id"] in seen_ids:
                problems["duplicate_ids"] += 1
            seen_ids.add(rec["id"])
            if rec.get("split") != split:
                problems["split_mismatch"] += 1
            if not (rec.get("text") or "").strip():
                problems["empty_texts"] += 1
            if not rec.get("label") or (valid_labels and rec["label"] not in valid_labels):
                problems["invalid_labels"] += 1
            if rec.get("label") in ("fake", "real", "0", "1") and valid_labels:
                problems["binary_label_leak"] += 1
            if rec["text_sha256"] in hashes:
                problems["within_split_duplicate_texts"] += 1
            hashes.add(rec["text_sha256"])
    return {"passed": not problems, "problems": dict(problems), "record_counts": counts}


def _write_report(path: Path, report: dict[str, Any]) -> None:
    write_json(path, report)


# --------------------------------------------------------------------------- #
# Dataset configuration
# --------------------------------------------------------------------------- #
_CONFIG: dict[str, dict[str, Any]] = {
    "liar": {
        "name": "LIAR",
        "prefix": "liar",
        "task": "english_political_statement_six_class_truthfulness",
        "files": LIAR_SPLIT_FILES,
        "reader": read_liar_rows,
        "report": "liar_audit.json",
        "clean_args": {
            "dataset_key": "liar", "id_prefix": "liar", "language": "en",
            "source_dataset": "LIAR",
            "text_field": "statement", "label_field": "label",
            "valid_labels": LIAR_LABELS,
            "label_scheme": "liar_6class_truthfulness",
            "task": "english_political_statement_six_class_truthfulness",
            "label_status": "original_six_class_unmapped",
            "label_source_by_split": {s: f for s, f in LIAR_SPLIT_FILES.items()},
            "id_field": "statement_id",
            "metadata_fields": ("subjects", "speaker", "speaker_job", "state", "party",
                                "barely_true_count", "false_count", "half_true_count",
                                "mostly_true_count", "pants_fire_count", "context"),
            "script_check": False,
        },
        "suitability": {
            "preprocessing": True,
            "binary_fake_real_training": False,
            "reason": "LIAR has six graded PolitiFact truthfulness labels on short political "
                      "statements, not full articles. No binary mapping is applied; any "
                      "mapping (e.g. how to treat half-true/barely-true/mostly-true) must be "
                      "a separate, documented, explicitly approved decision.",
            "suggested_task": "six-class (or approved-mapping) claim truthfulness classification",
        },
        "limitations": [
            "Statements are short claims, not news articles; models trained here may not transfer to article-level detection.",
            "Labels are PolitiFact editorial ratings, not independently re-verified here.",
            "Dataset is English only and US-politics focused.",
            "Speaker/credit-history metadata can leak label information; it is preserved under `metadata` but should be reviewed before use as features.",
            "README states research-use-only, provided as-is; check licensing before redistribution.",
            "Near-duplicate / paraphrase leakage was not analysed.",
        ],
    },
    "marathi_headlines": {
        "name": "Marathi headlines",
        "prefix": "marathi_headlines",
        "task": "marathi_headline_topic_classification",
        "files": MARATHI_SPLIT_FILES,
        "reader": read_marathi_rows,
        "report": "marathi_headlines_audit.json",
        "clean_args": {
            "dataset_key": "marathi_headlines", "id_prefix": "mrh", "language": "mr",
            "source_dataset": "Marathi_headlines_topic",
            "text_field": "headline", "label_field": "label",
            "valid_labels": None,  # categories are discovered, not assumed; empty is invalid
            "label_scheme": "news_topic_category",
            "task": "marathi_headline_topic_classification",
            "label_status": "topic_category_not_veracity",
            "label_source_by_split": {s: f for s, f in MARATHI_SPLIT_FILES.items()},
            "id_field": None,
            "metadata_fields": (),
            "script_check": True,
        },
        "suitability": {
            "preprocessing": True,
            "binary_fake_real_training": False,
            "reason": "Labels are news TOPIC categories (e.g. state/entertainment/sports), not "
                      "truthfulness. They must not be converted into Fake/Real. This is a "
                      "Marathi topic-classification dataset.",
            "suitability_for_veracity": "requires independently verified truthfulness labels",
        },
        "limitations": [
            "Topic labels carry no information about whether a headline is true or false.",
            "Headlines only; no article body, source, date, or URL provenance in the files.",
            "Only train/valid splits are provided; no test split was created.",
            "Class imbalance toward the `state` category.",
            "Dataset is licensed for open academic/research use.",
            "Near-duplicate / paraphrase leakage was not analysed; headline reuse across topics was only checked by exact normalized match.",
        ],
    },
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datasets", nargs="+", choices=list(_CONFIG), default=list(_CONFIG))
    ap.add_argument("--raw-root", type=Path, default=DATASETS_RAW)
    ap.add_argument("--processed-root", type=Path, default=DATASETS_PROCESSED)
    ap.add_argument("--quarantine-root", type=Path, default=DATASETS_QUARANTINE)
    ap.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    args = ap.parse_args()

    rc = 0
    print("Cleaning LIAR / Marathi-headline datasets (no binary relabeling)...")
    for kind in args.datasets:
        raw_dir = args.raw_root / kind
        report = process_dataset(kind, raw_dir, args.processed_root / kind,
                                 args.quarantine_root, args.reports_dir, args.processed_root)
        if report["errors"]:
            print(f"  ERRORS for {kind}: {report['errors']}")
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
