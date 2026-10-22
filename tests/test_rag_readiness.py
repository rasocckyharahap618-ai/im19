import unittest

from integrations.rag.readiness import (
    DEFAULT_DROPBOX_ROOT,
    classify_source_file,
    parse_health_payload,
    validate_source_root,
)


class RagReadinessTests(unittest.TestCase):
    def test_default_source_root_is_specific_and_absolute(self):
        self.assertEqual(
            validate_source_root(DEFAULT_DROPBOX_ROOT),
            "/Institutional_RAG/01_RAW_SOURCES",
        )

    def test_source_root_rejects_root_and_path_traversal(self):
        for value in ("", "/", "../private", "/Institutional_RAG/../private"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_source_root(value)

    def test_source_file_classifier_is_case_insensitive(self):
        self.assertEqual(classify_source_file("/folder/BOOK.PDF", 100, 1000), "supported")
        self.assertEqual(classify_source_file("/folder/notes.md", 100, 1000), "supported")
        self.assertEqual(classify_source_file("/folder/archive.zip", 100, 1000), "unsupported")

    def test_source_file_classifier_rejects_oversized_files(self):
        self.assertEqual(classify_source_file("/folder/book.pdf", 1001, 1000), "oversized")
        with self.assertRaises(ValueError):
            classify_source_file("/folder/book.pdf", 10, 0)

    def test_health_payload_requires_valid_nonnegative_counts(self):
        self.assertEqual(
            parse_health_payload({"status": "ok", "documents": 2, "chunks": 12}),
            {"documents": 2, "chunks": 12},
        )
        for payload in (
            None,
            {"status": "error", "documents": 1, "chunks": 1},
            {"status": "ok", "documents": -1, "chunks": 1},
            {"status": "ok", "documents": True, "chunks": 1},
            {"status": "ok", "documents": 1},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    parse_health_payload(payload)


if __name__ == "__main__":
    unittest.main()
