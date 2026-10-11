import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from fnd_common import (  # noqa: E402
    decode_text_bytes,
    infer_folder_label,
    is_macos_artifact,
    script_stats,
    text_sha256,
)


class MacosArtifactTests(unittest.TestCase):
    def test_skips_macosx_directory(self) -> None:
        path = ROOT / "datasets" / "raw" / "hindi" / "__MACOSX" / "Hindi_fake_news" / "._x.txt"
        self.assertTrue(is_macos_artifact(path))

    def test_keeps_normal_article(self) -> None:
        path = ROOT / "datasets" / "raw" / "hindi" / "Hindi_fake_news" / "Hindi_fake_news (1).txt"
        self.assertFalse(is_macos_artifact(path))


class LabelInferenceTests(unittest.TestCase):
    def test_fake_folder(self) -> None:
        path = Path("hindi") / "Hindi_fake_news" / "a.txt"
        self.assertEqual(infer_folder_label(path), "fake")

    def test_real_folder(self) -> None:
        path = Path("marathi") / "Marathi_real_news" / "a.txt"
        self.assertEqual(infer_folder_label(path), "real")

    def test_unknown_without_keywords(self) -> None:
        path = Path("misc") / "articles" / "a.txt"
        self.assertEqual(infer_folder_label(path), "unknown")

    def test_filename_does_not_override_folder(self) -> None:
        path = Path("marathi") / "Marathi_real_news" / "same_as_fake.txt"
        self.assertEqual(infer_folder_label(path), "real")

    def test_project_folder_named_fake_does_not_poison_real_labels(self) -> None:
        path = (
            Path("C:/Users/Lenovo/Downloads/FakeNewsDetection")
            / "datasets"
            / "raw"
            / "hindi"
            / "Hindi_real_news"
            / "article.txt"
        )
        self.assertEqual(infer_folder_label(path), "real")


class HashAndScriptTests(unittest.TestCase):
    def test_hash_ignores_whitespace(self) -> None:
        self.assertEqual(text_sha256("hello   world"), text_sha256("hello world"))

    def test_devanagari_ratio(self) -> None:
        stats = script_stats("यह खबर है")
        self.assertGreater(stats["devanagari_ratio"], 0.9)
        self.assertEqual(stats["latin_chars"], 0)

    def test_utf8_decode(self) -> None:
        text, encoding, replaced = decode_text_bytes("नमस्ते".encode("utf-8"))
        self.assertEqual(text, "नमस्ते")
        self.assertEqual(encoding, "utf-8-sig")
        self.assertFalse(replaced)


if __name__ == "__main__":
    unittest.main()
