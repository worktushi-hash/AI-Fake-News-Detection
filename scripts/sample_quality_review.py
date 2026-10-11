"""Reproducible quality sampling log generator."""

from __future__ import annotations

import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fnd_common import (
    DATASETS_PROCESSED,
    REPORTS_DIR,
    read_jsonl,
    write_text,
)


def sample_dataset(
    jsonl_path: Path, lang: str, sample_per_class: int = 5, seed: int = 42
) -> list[dict]:
    if not jsonl_path.is_file():
        return []

    records_by_label = defaultdict(list)
    for rec in read_jsonl(jsonl_path):
        records_by_label[str(rec.get("label"))].append(rec)

    random.seed(seed)
    sampled = []
    for label, items in sorted(records_by_label.items()):
        take = min(len(items), sample_per_class)
        sampled.extend(random.sample(items, take))

    return sampled


def main() -> int:
    print("Generating quality review sample log...")

    samples_en = sample_dataset(DATASETS_PROCESSED / "english" / "english_clean.jsonl", "en")
    samples_hi = sample_dataset(DATASETS_PROCESSED / "hindi" / "hindi_clean.jsonl", "hi")
    samples_mr = sample_dataset(DATASETS_PROCESSED / "marathi" / "marathi_clean.jsonl", "mr")

    lines = [
        "# Manual Quality Sample Review Log",
        "",
        "**Note on Status**: This document contains a seeded, reproducible random sample drawn for human review.",
        "Generating this sample log is an automated quality check helper; human qualitative assessment of these sampled records is **pending / ongoing**.",
        "",
        "- Random seed: `42`",
        "- Target sample per class: `5`",
        "",
        "## Sampled English Records (WELFake)",
        "",
    ]

    for s in samples_en:
        lines.append(f"### ID `{s['id']}` (Label `{s['label']}` / Status `{s['label_status']}`)")
        lines.append(f"- **Source ID**: `{s['source_record_id']}`")
        lines.append(f"- **Title**: {s['title']}")
        lines.append(f"- **Text Preview**: {s['text'][:200]}...")
        lines.append("")

    lines.append("## Sampled Hindi Records")
    lines.append("")
    for s in samples_hi:
        lines.append(f"### ID `{s['id']}` (Label `{s['label']}` / Status `{s['label_status']}`)")
        lines.append(f"- **Source ID**: `{s['source_record_id']}`")
        lines.append(f"- **Text Preview**: {s['text'][:200]}...")
        lines.append("")

    lines.append("## Sampled Marathi Records")
    lines.append("")
    for s in samples_mr:
        lines.append(f"### ID `{s['id']}` (Label `{s['label']}` / Status `{s['label_status']}`)")
        lines.append(f"- **Source ID**: `{s['source_record_id']}`")
        lines.append(f"- **Text Preview**: {s['text'][:200]}...")
        lines.append("")

    lines.extend([
        "## Pending Human Review Instructions",
        "",
        "1. **English**: Review 10 sampled articles for text formatting, title alignment, and source markers.",
        "2. **Hindi**: Verify 10 sampled Devanagari articles for script correctness and readability.",
        "3. **Marathi**: Verify 10 sampled Devanagari Marathi articles for language accuracy.",
        "",
    ])

    report_path = REPORTS_DIR / "manual_sample_review.md"
    write_text(report_path, "\n".join(lines))
    print(f"Wrote manual quality sample review log to {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
