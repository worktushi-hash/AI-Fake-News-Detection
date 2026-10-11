"""Shared helpers for Fake News Detection dataset scripts.

These functions are intentionally standard-library only so the audit
pipeline can run before pandas, scikit-learn, or PyTorch are installed.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Generator, Iterable

ROOT = Path(__file__).resolve().parent.parent
DATASETS_RAW = ROOT / "datasets" / "raw"
DATASETS_PROCESSED = ROOT / "datasets" / "processed"
DATASETS_QUARANTINE = ROOT / "datasets" / "quarantine"
REPORTS_DIR = ROOT / "reports"

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
LATIN_RE = re.compile(r"[A-Za-z]")
URL_RE = re.compile(r"https?://", re.IGNORECASE)

SKIP_DIR_NAMES = {"__macosx"}
SKIP_FILE_NAMES = {".ds_store", "thumbs.db"}

# Primes for 128 MinHash permutations
_MINHASH_A = [((i * 2654435761 + 1013904223) & 0xFFFFFFFF) for i in range(128)]
_MINHASH_B = [((i * 1597334677 + 104729) & 0xFFFFFFFF) for i in range(128)]
_PRIME_32 = 4294967291


def project_root() -> Path:
    return ROOT


def is_macos_artifact(path: Path) -> bool:
    """Return True for unzip leftovers that are not news articles."""
    parts_lower = {part.lower() for part in path.parts}
    if SKIP_DIR_NAMES & parts_lower:
        return True
    name = path.name
    if name.startswith("._"):
        return True
    if name.lower() in SKIP_FILE_NAMES:
        return True
    return False


def infer_folder_label(path: Path) -> str:
    """Infer fake/real from the immediate parent folder only."""
    name = path.parent.name.lower()
    has_fake = "fake" in name
    has_real = "real" in name
    if has_fake and has_real:
        return "unknown"
    if has_fake:
        return "fake"
    if has_real:
        return "real"
    return "unknown"


def normalize_for_hash(text: str) -> str:
    """Whitespace-normalize and NFC-normalize text."""
    collapsed = " ".join(text.split())
    return unicodedata.normalize("NFC", collapsed)


def text_sha256(text: str) -> str:
    payload = normalize_for_hash(text).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def minhash_signature(text: str, k: int = 5, num_perm: int = 128) -> list[int]:
    """Compute MinHash signature of text using k-character shingling."""
    normalized = normalize_for_hash(text).lower()
    if len(normalized) < k:
        shingles = {normalized} if normalized else {""}
    else:
        shingles = {normalized[i : i + k] for i in range(len(normalized) - k + 1)}

    sig = [0xFFFFFFFF] * num_perm
    for shingle in shingles:
        # Hash shingle to a 32-bit integer
        h_val = int(hashlib.md5(shingle.encode("utf-8")).hexdigest()[:8], 16)
        for i in range(num_perm):
            perm_h = (_MINHASH_A[i] * h_val + _MINHASH_B[i]) % _PRIME_32
            if perm_h < sig[i]:
                sig[i] = perm_h
    return sig


def jaccard_similarity(sig1: list[int], sig2: list[int]) -> float:
    """Estimate Jaccard similarity from two MinHash signatures."""
    if not sig1 or not sig2 or len(sig1) != len(sig2):
        return 0.0
    matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
    return matches / len(sig1)


def script_stats(text: str) -> dict[str, Any]:
    """Count Devanagari vs Latin letters."""
    devanagari = len(DEVANAGARI_RE.findall(text))
    latin = len(LATIN_RE.findall(text))
    total = devanagari + latin
    return {
        "devanagari_chars": devanagari,
        "latin_chars": latin,
        "letter_chars": total,
        "devanagari_ratio": (devanagari / total) if total else 0.0,
        "latin_ratio": (latin / total) if total else 0.0,
        "contains_url": bool(URL_RE.search(text)),
    }


def decode_text_bytes(data: bytes) -> tuple[str, str, bool]:
    """Try common encodings. Returns (text, encoding_name, used_replacement)."""
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return data.decode(encoding), encoding, False
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replace", True


def read_text_file(path: Path) -> tuple[str, str, bool]:
    return decode_text_bytes(path.read_bytes())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    """Write records to a line-delimited JSON file. Returns record count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> Generator[dict[str, Any], None, None]:
    """Stream records from a line-delimited JSON file."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()
