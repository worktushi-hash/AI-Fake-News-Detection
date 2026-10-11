"""Verify SHA-256 hashes of raw dataset files against a saved baseline manifest."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS_RAW = ROOT / "datasets" / "raw"
REPORTS_DIR = ROOT / "reports"
BASELINE_MANIFEST = REPORTS_DIR / "raw_baseline_hashes.json"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_current_hashes() -> dict[str, str]:
    if not DATASETS_RAW.is_dir():
        raise FileNotFoundError(f"Raw datasets folder not found: {DATASETS_RAW}")

    hashes = {}
    print("Computing current SHA-256 hashes for raw files...")

    # English CSV
    csv_path = DATASETS_RAW / "english" / "WELFake_Dataset.csv"
    if csv_path.is_file():
        hashes[str(csv_path.relative_to(ROOT)).replace("\\", "/")] = file_sha256(csv_path)

    # Hindi & Marathi txt files
    for lang in ("hindi", "marathi"):
        lang_dir = DATASETS_RAW / lang
        if lang_dir.is_dir():
            for p in lang_dir.rglob("*"):
                if p.is_file():
                    rel = str(p.relative_to(ROOT)).replace("\\", "/")
                    hashes[rel] = file_sha256(p)

    return hashes


def verify_against_baseline(current_hashes: dict[str, str]) -> tuple[bool, str]:
    if not BASELINE_MANIFEST.is_file():
        # Save baseline manifest on first execution
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        BASELINE_MANIFEST.write_text(
            json.dumps(current_hashes, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return True, f"Saved initial baseline hash manifest with {len(current_hashes)} files to {BASELINE_MANIFEST.name}."

    baseline_hashes = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))

    mismatches = []
    missing_in_current = []
    new_files = []

    for path, b_hash in baseline_hashes.items():
        if path not in current_hashes:
            missing_in_current.append(path)
        elif current_hashes[path] != b_hash:
            mismatches.append(path)

    for path in current_hashes:
        if path not in baseline_hashes:
            new_files.append(path)

    if mismatches or missing_in_current or new_files:
        msg = f"FAILED integrity verification: {len(mismatches)} altered, {len(missing_in_current)} missing, {len(new_files)} new files."
        return False, msg

    return True, f"PASSED: All {len(current_hashes)} raw files match the saved baseline manifest exactly."


def write_integrity_report(current_hashes: dict[str, str], status_msg: str, output_path: Path) -> None:
    lines = [
        "# Raw Dataset File Integrity Verification Report",
        "",
        "This report records cryptographic SHA-256 hashes and baseline verification results.",
        "",
        f"- Baseline Status: **{status_msg}**",
        f"- Total raw files tracked: **{len(current_hashes):,}**",
        "",
        "## Key File Hash Summary",
        "",
        "| Relative File Path | File Size (Bytes) | SHA-256 Hash |",
        "| :--- | :--- | :--- |",
    ]

    for rel_path in sorted(current_hashes.keys()):
        if "WELFake_Dataset.csv" in rel_path:
            abs_path = ROOT / rel_path
            size = abs_path.stat().st_size
            digest = current_hashes[rel_path]
            lines.append(f"| `{rel_path}` | {size:,} | `{digest}` |")

    lines.extend([
        "",
        "## Summary Counts by Language Corpus",
        "",
        f"- English raw files: **{sum(1 for p in current_hashes if 'english' in p)}**",
        f"- Hindi raw files: **{sum(1 for p in current_hashes if 'hindi' in p)}**",
        f"- Marathi raw files: **{sum(1 for p in current_hashes if 'marathi' in p)}**",
        "",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote raw integrity report to {output_path}")


def main() -> int:
    hashes = compute_current_hashes()
    passed, msg = verify_against_baseline(hashes)
    print(msg)
    report_path = REPORTS_DIR / "raw_file_integrity.md"
    write_integrity_report(hashes, msg, report_path)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
