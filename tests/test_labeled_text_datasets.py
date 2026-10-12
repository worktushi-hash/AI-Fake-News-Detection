"""Tests for LIAR / Marathi-headline cleaning. Uses small synthetic fixtures only."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from clean_labeled_text_datasets import (  # noqa: E402
    LIAR_LABELS,
    process_dataset,
    read_liar_rows,
    read_marathi_rows,
)
from fnd_common import file_sha256, read_jsonl  # noqa: E402


def liar_line(i, label, stmt):
    return "\t".join([f"{i}.json", label, stmt, "health", "someone", "job", "Texas", "none",
                      "0", "1", "0", "0", "0", "a speech"])


def run(kind, raw_files):
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    raw = root / "raw" / kind
    raw.mkdir(parents=True)
    for name, content in raw_files.items():
        (raw / name).write_text(content, encoding="utf-8")
    hashes = {n: file_sha256(raw / n) for n in raw_files}
    rep = process_dataset(kind, raw, root / "processed" / kind, root / "quarantine",
                          root / "reports", root / "processed")
    return tmp, root, rep, hashes


def load(root, kind, split):
    return list(read_jsonl(root / "processed" / kind / f"{kind}_{split}_clean.jsonl"))


class LiarTests(unittest.TestCase):
    def setUp(self):
        quoted = 'He said "hello"  to   everyone.'
        self.tmp, self.root, self.rep, self.hashes = run("liar", {
            "train.tsv": "\n".join([
                liar_line(1, "pants-fire", quoted),
                liar_line(2, "half-true", "Unique statement one."),
                liar_line(3, "false", "Same text."),
                liar_line(4, "false", "Same   text."),          # same-label dup (whitespace differs)
                liar_line(5, "true", "Conflict text."),
                liar_line(6, "false", "Conflict text."),        # conflicting labels -> quarantine
                liar_line(7, "mostly-true", "   "),             # missing statement
                liar_line(8, "bogus-label", "Bad label."),      # invalid label
                "only\ttwo",                                    # malformed
            ]) + "\n",
            "valid.tsv": liar_line(10, "barely-true", "Shared across splits.") + "\n",
            "test.tsv": liar_line(11, "barely-true", "Shared across splits.") + "\n",
        })

    def tearDown(self):
        self.tmp.cleanup()

    def test_counts_and_reasons(self):
        r = self.rep
        self.assertEqual(r["per_split"]["train"]["records_read"], 9)
        self.assertEqual(r["exclusion_reasons"], {
            "missing_text": 1, "invalid_label": 1, "malformed_row": 1, "exact_duplicate": 1})
        self.assertEqual(r["records_quarantined"], 2)
        self.assertTrue(r["accounting_balanced"])
        self.assertEqual(r["invalid_label_counts"], {"bogus-label": 1})
        self.assertEqual(r["errors"], [])

    def test_original_text_and_labels_preserved(self):
        recs = {x["source_record_id"]: x for x in load(self.root, "liar", "train")}
        self.assertEqual(recs["1.json"]["text"], 'He said "hello"  to   everyone.')
        self.assertEqual(recs["1.json"]["label"], "pants-fire")
        self.assertEqual(recs["1.json"]["metadata"]["speaker"], "someone")
        for rec in load(self.root, "liar", "train"):
            self.assertIn(rec["label"], LIAR_LABELS)

    def test_no_binary_conversion(self):
        labels = {x["label"] for s in ("train", "valid", "test") for x in load(self.root, "liar", s)}
        self.assertTrue(labels <= set(LIAR_LABELS))
        self.assertNotIn("fake", labels)
        self.assertNotIn("real", labels)
        self.assertEqual(self.rep["suitability"]["binary_fake_real_training"], False)

    def test_within_split_dup_keeps_first(self):
        ids = [x["source_record_id"] for x in load(self.root, "liar", "train")]
        self.assertIn("3.json", ids)
        self.assertNotIn("4.json", ids)
        self.assertNotIn("5.json", ids)
        self.assertNotIn("6.json", ids)

    def test_cross_split_reported_not_moved(self):
        self.assertEqual(self.rep["duplicates"]["cross_split"]["groups_total"], 1)
        self.assertEqual(self.rep["duplicates"]["cross_split"]["pair_counts"], {"test__valid": 1})
        v = load(self.root, "liar", "valid")
        t = load(self.root, "liar", "test")
        self.assertEqual((len(v), len(t)), (1, 1))
        self.assertTrue(v[0]["cross_split_duplicate"])
        self.assertEqual(v[0]["split"], "valid")
        self.assertEqual(t[0]["split"], "test")

    def test_raw_unmodified_and_validation(self):
        self.assertFalse(self.rep["raw_files_modified"])
        self.assertTrue(self.rep["validation"]["passed"])
        for name, h in self.hashes.items():
            self.assertEqual(file_sha256(self.root / "raw" / "liar" / name), h)

    def test_reader_literal_quotes_and_columns(self):
        rows, bad, cols = read_liar_rows(self.root / "raw" / "liar" / "train.tsv")
        self.assertEqual(len(cols), 14)
        self.assertEqual(len(bad), 1)
        self.assertEqual(rows[0]["statement"], 'He said "hello"  to   everyone.')

    def test_report_is_json_serialisable(self):
        json.dumps(self.rep, ensure_ascii=False)


class MarathiTests(unittest.TestCase):
    def setUp(self):
        dup = "सचिन तेंडुलकरने आठवणींना दिला उजाळा"
        self.tmp, self.root, self.rep, _ = run("marathi_headlines", {
            "train.csv": (
                "headline,label\n"
                f'"{dup}, पुन्हा",state\n'                       # comma inside quotes
                "पुण्यात आघाडीचा पोपट पुन्हा जिवंत !,state\n"
                "पुण्यात  आघाडीचा पोपट पुन्हा जिवंत !,state\n"   # whitespace dup, same label
                "दोन विषय असलेली बातमी,sports\n"
                "दोन विषय असलेली बातमी,entertainment\n"        # conflicting labels
                "   ,sports\n"                                  # whitespace-only headline
                "Only English words here,sports\n"              # no Devanagari
                "IPL मधील विजय,sports\n"                       # mixed script retained
                "बातमी,\n"                                      # empty label
            ),
            "valid.csv": (
                "headline,label\n"
                "पुण्यात आघाडीचा पोपट पुन्हा जिवंत !,state\n"    # cross-split duplicate
                "नवी बातमी,entertainment\n"
            ),
        })

    def tearDown(self):
        self.tmp.cleanup()

    def test_devanagari_and_punctuation_preserved(self):
        recs = load(self.root, "marathi_headlines", "train")
        texts = [r["text"] for r in recs]
        self.assertIn("सचिन तेंडुलकरने आठवणींना दिला उजाळा, पुन्हा", texts)
        self.assertIn("पुण्यात आघाडीचा पोपट पुन्हा जिवंत !", texts)
        self.assertIn("IPL मधील विजय", texts)
        raw = (self.root / "processed" / "marathi_headlines" / "marathi_headlines_train_clean.jsonl"
               ).read_text(encoding="utf-8")
        self.assertIn("तेंडुलकरने", raw)  # not \u-escaped, not transliterated

    def test_categories_preserved_not_binary(self):
        for s in ("train", "valid"):
            for r in load(self.root, "marathi_headlines", s):
                self.assertIn(r["label"], {"state", "sports", "entertainment"})
                self.assertEqual(r["label_status"], "topic_category_not_veracity")
        self.assertFalse(self.rep["suitability"]["binary_fake_real_training"])

    def test_exclusions_and_quarantine(self):
        self.assertEqual(self.rep["exclusion_reasons"], {
            "missing_text": 1, "no_devanagari": 1, "invalid_label": 1, "exact_duplicate": 1})
        self.assertEqual(self.rep["records_quarantined"], 2)
        self.assertTrue(self.rep["accounting_balanced"])

    def test_cross_split_and_split_preservation(self):
        self.assertEqual(self.rep["duplicates"]["cross_split"]["groups_total"], 1)
        valid = load(self.root, "marathi_headlines", "valid")
        self.assertEqual(len(valid), 2)
        self.assertTrue(all(r["split"] == "valid" for r in valid))
        self.assertFalse((self.root / "processed" / "marathi_headlines" /
                          "marathi_headlines_test_clean.jsonl").exists())

    def test_validation_passes(self):
        self.assertTrue(self.rep["validation"]["passed"], self.rep["validation"])


class EdgeCaseTests(unittest.TestCase):
    def test_empty_files(self):
        tmp, root, rep, _ = run("marathi_headlines", {"train.csv": "headline,label\n",
                                                      "valid.csv": "headline,label\n"})
        with tmp:
            self.assertEqual(rep["records_retained"], 0)
            self.assertEqual(len(rep["warnings"]), 2)
            self.assertEqual(rep["errors"], [])

    def test_wrong_columns_reported_not_crashing(self):
        tmp, root, rep, _ = run("marathi_headlines", {"train.csv": "a,b\n1,2\n",
                                                      "valid.csv": "headline,label\nबातमी,state\n"})
        with tmp:
            self.assertTrue(any("expected columns" in e for e in rep["errors"]))
            self.assertEqual(rep["records_retained"], 1)

    def test_missing_dataset_does_not_fabricate(self):
        with tempfile.TemporaryDirectory() as t:
            rep = process_dataset("liar", Path(t) / "nope", Path(t) / "o", Path(t) / "q",
                                  Path(t) / "r", Path(t) / "p")
            self.assertEqual(rep["status"], "not_run_no_input")
            self.assertTrue(rep["errors"])
            self.assertNotIn("records_retained", rep)

    def test_short_marathi_row_malformed(self):
        tmp = tempfile.TemporaryDirectory()
        p = Path(tmp.name) / "t.csv"
        p.write_text("headline,label\nफक्त एक\nबातमी,state\n", encoding="utf-8")
        rows, bad, _ = read_marathi_rows(p)
        tmp.cleanup()
        self.assertEqual((len(rows), len(bad)), (1, 1))


class LeakageResolutionTests(unittest.TestCase):
    def test_leakage_resolution_verifies_zero_cross_split_overlap(self):
        tmp, root, rep, _ = run("liar", {
            "train.tsv": liar_line(1, "false", "Shared text across splits.") + "\n",
            "valid.tsv": liar_line(2, "false", "Shared text across splits.") + "\n",
            "test.tsv": liar_line(3, "false", "Shared text across splits.") + "\n",
        })
        with tmp:
            self.assertTrue(rep["leakage_resolution"]["verification_passed"])
            self.assertEqual(rep["leakage_resolution"]["cross_split_groups_after"], 0)
            train_no_leak = list(read_jsonl(root / "processed" / "liar" / "liar_train_no_leakage_clean.jsonl"))
            valid_no_leak = list(read_jsonl(root / "processed" / "liar" / "liar_valid_no_leakage_clean.jsonl"))
            self.assertEqual(len(train_no_leak), 0)
            self.assertEqual(len(valid_no_leak), 1)


class BackwardCompatTests(unittest.TestCase):
    def test_existing_helpers_unchanged(self):
        from fnd_common import normalize_for_hash, text_sha256
        self.assertEqual(text_sha256("a   b"), text_sha256("a b"))
        self.assertEqual(normalize_for_hash("e\u0301"), "\u00e9")

    def test_existing_scripts_still_import(self):
        import clean_dataset_pipeline, validate_processed_datasets, verify_raw_integrity  # noqa: F401


if __name__ == "__main__":
    unittest.main()

