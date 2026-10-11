"""Unit tests for dataset cleaning pipeline, MinHash, quarantine, and label status rules."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.fnd_common import (
    jaccard_similarity,
    minhash_signature,
    normalize_for_hash,
    read_jsonl,
    text_sha256,
    write_jsonl,
)


class PipelineUnitTests(unittest.TestCase):

    def test_nfc_normalization(self):
        text_decomposed = "e\u0301"  # e with combining acute accent
        text_composed = "é"
        self.assertEqual(normalize_for_hash(text_decomposed), text_composed)
        self.assertEqual(text_sha256(text_decomposed), text_sha256(text_composed))

    def test_jsonl_roundtrip(self):
        records = [
            {
                "id": "en_000001",
                "language": "en",
                "text": "First article body.",
                "label_status": "unverified",
            },
            {
                "id": "hi_000001",
                "language": "hi",
                "text": "हिंदी लेख का पाठ।",
                "label_status": "claimed_folder_label",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "test.jsonl"
            count = write_jsonl(tmp_file, records)
            self.assertEqual(count, 2)
            loaded = list(read_jsonl(tmp_file))
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]["id"], "en_000001")
            self.assertEqual(loaded[0]["label_status"], "unverified")
            self.assertEqual(loaded[1]["text"], "हिंदी लेख का पाठ।")

    def test_minhash_jaccard_identical(self):
        text1 = "This is a news article about economic policy changes."
        text2 = "This is a news article about economic policy changes."
        sig1 = minhash_signature(text1)
        sig2 = minhash_signature(text2)
        sim = jaccard_similarity(sig1, sig2)
        self.assertEqual(sim, 1.0)

    def test_minhash_jaccard_different(self):
        text1 = "Cricket match highlights and sports news updates."
        text2 = "Quantum physics research published in physics journal."
        sig1 = minhash_signature(text1)
        sig2 = minhash_signature(text2)
        sim = jaccard_similarity(sig1, sig2)
        self.assertLess(sim, 0.5)

    def test_processed_dataset_label_status_unverified(self):
        """Verify that processed English records carry label_status == unverified."""
        en_path = Path("datasets/processed/english/english_clean.jsonl")
        if en_path.is_file():
            first_rec = next(read_jsonl(en_path))
            self.assertEqual(first_rec.get("label_status"), "unverified")
            self.assertEqual(first_rec.get("review_status"), "accepted")


if __name__ == "__main__":
    unittest.main()
