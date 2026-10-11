import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_txt_corpus import audit_language  # noqa: E402
from inspect_english import audit_english_csv  # noqa: E402


class FolderCorpusAuditTests(unittest.TestCase):
    def test_counts_skips_artifacts_and_finds_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = root / "Demo_fake_news"
            real = root / "Demo_real_news"
            junk = root / "__MACOSX" / "Demo_fake_news"
            fake.mkdir(parents=True)
            real.mkdir(parents=True)
            junk.mkdir(parents=True)

            (fake / "a.txt").write_text("यह एक खबर है जो पर्याप्त लंबी है।", encoding="utf-8")
            (fake / "a_copy.txt").write_text("यह एक खबर है जो पर्याप्त लंबी है।", encoding="utf-8")
            (real / "same_as_fake.txt").write_text(
                "यह एक खबर है जो पर्याप्त लंबी है।", encoding="utf-8"
            )
            (real / "empty.txt").write_text("   \n", encoding="utf-8")
            (junk / "._ignored.txt").write_text("should skip", encoding="utf-8")
            (fake / "notes.md").write_text("not an article", encoding="utf-8")

            report = audit_language("demo", root)

            self.assertEqual(report["article_txt_files"], 4)
            self.assertEqual(report["artifact_files_skipped"], 1)
            self.assertEqual(report["folder_label_counts"]["fake"], 2)
            self.assertEqual(report["folder_label_counts"]["real"], 2)
            self.assertEqual(report["empty_files"], 1)
            self.assertEqual(report["conflicting_label_groups"], 1)
            self.assertGreaterEqual(report["duplicate_groups"], 1)
            self.assertEqual(report["issue_counts"]["non_txt"], 1)
            self.assertFalse(report["raw_files_modified"])


class EnglishCsvAuditTests(unittest.TestCase):
    def test_tiny_csv_duplicate_and_blank_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "tiny.csv"
            csv_path.write_text(
                ",title,text,label\n"
                "0,Hello,This is a long enough article text for hashing.,0\n"
                "1,,This is a long enough article text for hashing.,1\n"
                "2,Other,A completely different article used as control text.,1\n",
                encoding="utf-8",
            )
            report = audit_english_csv(csv_path)
            self.assertEqual(report["parsed_records"], 3)
            self.assertEqual(report["label_counts"]["0"], 1)
            self.assertEqual(report["label_counts"]["1"], 2)
            self.assertEqual(report["missing_or_blank"]["title"], 1)
            self.assertEqual(report["conflicting_label_groups"], 1)
            self.assertEqual(report["label_mapping_status"], "unverified")
            json.dumps(report["examples"])


if __name__ == "__main__":
    unittest.main()
