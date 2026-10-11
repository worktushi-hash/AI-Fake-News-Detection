"""Audit Hindi/Marathi folder corpora without modifying raw files.

Example:
    python scripts/audit_txt_corpus.py
    python scripts/audit_txt_corpus.py --language hindi
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fnd_common import (
    DATASETS_RAW,
    REPORTS_DIR,
    infer_folder_label,
    is_macos_artifact,
    read_text_file,
    script_stats,
    text_sha256,
    write_json,
    write_text,
)

LANGUAGE_DIRS = {
    "hindi": DATASETS_RAW / "hindi",
    "marathi": DATASETS_RAW / "marathi",
}

SHORT_CHAR_THRESHOLD = 50
MAX_EXAMPLES = 15


def audit_language(language: str, root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise FileNotFoundError(f"Dataset folder not found: {root}")

    label_counts: Counter[str] = Counter()
    encoding_counts: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    issues: dict[str, list[str]] = defaultdict(list)
    issue_counts: Counter[str] = Counter()
    hash_to_records: dict[str, list[dict[str, str]]] = defaultdict(list)

    artifact_files = 0
    article_files = 0
    replacement_decodes = 0
    empty_files = 0
    short_files = 0
    unknown_label_files = 0
    url_files = 0
    low_devanagari_files = 0
    byte_total = 0
    char_total = 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if is_macos_artifact(path):
            artifact_files += 1
            continue

        suffix = path.suffix.lower() or "(none)"
        extension_counts[suffix] += 1
        if suffix != ".txt":
            _add_issue(issues, issue_counts, "non_txt", rel)
            continue

        article_files += 1
        byte_total += path.stat().st_size
        label = infer_folder_label(path)
        label_counts[label] += 1
        if label == "unknown":
            unknown_label_files += 1
            _add_issue(issues, issue_counts, "unknown_label", rel)

        text, encoding, used_replacement = read_text_file(path)
        encoding_counts[encoding] += 1
        if used_replacement:
            replacement_decodes += 1
            _add_issue(issues, issue_counts, "replacement_decode", rel)

        stripped = text.strip()
        char_total += len(stripped)
        if not stripped:
            empty_files += 1
            _add_issue(issues, issue_counts, "empty", rel)
            continue
        if len(stripped) < SHORT_CHAR_THRESHOLD:
            short_files += 1
            _add_issue(issues, issue_counts, "short", rel)

        stats = script_stats(stripped)
        if stats["contains_url"]:
            url_files += 1
        if stats["letter_chars"] >= 20 and stats["devanagari_ratio"] < 0.5:
            low_devanagari_files += 1
            _add_issue(issues, issue_counts, "low_devanagari", rel)

        digest = text_sha256(stripped)
        hash_to_records[digest].append(
            {
                "path": rel,
                "label": label,
            }
        )

    duplicate_groups = []
    conflicting_groups = []
    extra_duplicate_copies = 0
    for digest, records in hash_to_records.items():
        if len(records) < 2:
            continue
        extra_duplicate_copies += len(records) - 1
        labels = sorted({item["label"] for item in records})
        group = {
            "sha256": digest,
            "count": len(records),
            "labels": labels,
            "paths": [item["path"] for item in records[:MAX_EXAMPLES]],
        }
        duplicate_groups.append(group)
        if len(labels) > 1:
            conflicting_groups.append(group)

    duplicate_groups.sort(key=lambda item: item["count"], reverse=True)
    conflicting_groups.sort(key=lambda item: item["count"], reverse=True)

    report = {
        "language": language,
        "raw_root": str(root),
        "raw_files_modified": False,
        "artifact_files_skipped": artifact_files,
        "article_txt_files": article_files,
        "folder_label_counts": dict(label_counts),
        "encoding_counts": dict(encoding_counts),
        "extension_counts": dict(extension_counts),
        "empty_files": empty_files,
        "short_files_under_chars": {
            "threshold": SHORT_CHAR_THRESHOLD,
            "count": short_files,
        },
        "unknown_label_files": unknown_label_files,
        "replacement_decodes": replacement_decodes,
        "files_containing_url": url_files,
        "low_devanagari_files": low_devanagari_files,
        "unique_normalized_texts": len(hash_to_records),
        "duplicate_groups": len(duplicate_groups),
        "extra_duplicate_copies": extra_duplicate_copies,
        "conflicting_label_groups": len(conflicting_groups),
        "bytes_in_article_files": byte_total,
        "chars_in_non_empty_articles": char_total,
        "notes": [
            "Folder names are treated as claimed labels, not verified ground truth.",
            "Hindi and Marathi both use Devanagari; script ratio is not a language ID.",
            "Exact-hash duplicates do not prove that near-duplicates or leakage are absent.",
            "__MACOSX and ._* files are OS artifacts and were not counted as articles.",
        ],
        "examples": {
            "empty": issues["empty"],
            "short": issues["short"],
            "unknown_label": issues["unknown_label"],
            "replacement_decode": issues["replacement_decode"],
            "non_txt": issues["non_txt"],
            "low_devanagari": issues["low_devanagari"],
            "largest_duplicate_groups": duplicate_groups[:MAX_EXAMPLES],
            "conflicting_label_groups": conflicting_groups[:MAX_EXAMPLES],
        },
        "issue_counts": dict(issue_counts),
    }
    return report


def _add_issue(
    issues: dict[str, list[str]],
    issue_counts: Counter[str],
    kind: str,
    rel: str,
) -> None:
    issue_counts[kind] += 1
    if len(issues[kind]) < MAX_EXAMPLES:
        issues[kind].append(rel)


def render_markdown(report: dict[str, Any]) -> str:
    labels = report["folder_label_counts"]
    lines = [
        f"# {report['language'].title()} folder corpus audit",
        "",
        "Raw files were not modified.",
        "",
        f"- Article `.txt` files counted: **{report['article_txt_files']}**",
        f"- macOS/OS artifacts skipped: **{report['artifact_files_skipped']}**",
        f"- Claimed fake: **{labels.get('fake', 0)}**",
        f"- Claimed real: **{labels.get('real', 0)}**",
        f"- Unknown folder label: **{labels.get('unknown', 0)}**",
        f"- Empty files: **{report['empty_files']}**",
        f"- Short files (< {report['short_files_under_chars']['threshold']} chars): **{report['short_files_under_chars']['count']}**",
        f"- Unique normalized texts: **{report['unique_normalized_texts']}**",
        f"- Duplicate groups: **{report['duplicate_groups']}**",
        f"- Extra duplicate copies: **{report['extra_duplicate_copies']}**",
        f"- Same text, different folder labels: **{report['conflicting_label_groups']}**",
        f"- Decode-with-replacement files: **{report['replacement_decodes']}**",
        f"- Low Devanagari ratio files: **{report['low_devanagari_files']}**",
        f"- Files containing `http://` or `https://`: **{report['files_containing_url']}**",
        "",
        "## Encodings",
        "",
    ]
    for encoding, count in sorted(report["encoding_counts"].items()):
        lines.append(f"- `{encoding}`: {count}")
    lines.extend(["", "## Notes", ""])
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.extend(["", "## Example conflicting-label groups", ""])
    conflicts = report["examples"]["conflicting_label_groups"]
    if not conflicts:
        lines.append("None found among exact-hash duplicates.")
    else:
        for group in conflicts:
            lines.append(
                f"- hash `{group['sha256'][:12]}...` count={group['count']} labels={group['labels']}"
            )
            for path in group["paths"]:
                lines.append(f"  - {path}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Hindi/Marathi txt corpora.")
    parser.add_argument(
        "--language",
        choices=("hindi", "marathi", "all"),
        default="all",
        help="Which folder corpus to audit.",
    )
    args = parser.parse_args(argv)

    languages = list(LANGUAGE_DIRS) if args.language == "all" else [args.language]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    for language in languages:
        root = LANGUAGE_DIRS[language]
        print(f"Auditing {language} at {root} ...")
        report = audit_language(language, root)
        json_path = REPORTS_DIR / f"audit_{language}.json"
        md_path = REPORTS_DIR / f"audit_{language}.md"
        write_json(json_path, report)
        write_text(md_path, render_markdown(report))
        print(
            f"  txt={report['article_txt_files']} "
            f"fake={report['folder_label_counts'].get('fake', 0)} "
            f"real={report['folder_label_counts'].get('real', 0)} "
            f"empty={report['empty_files']} "
            f"dup_groups={report['duplicate_groups']} "
            f"conflicts={report['conflicting_label_groups']}"
        )
        print(f"  wrote {json_path}")
        print(f"  wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
