import math
import unittest
from unittest.mock import patch

from integrations.rag.ingest import (
    DEFAULT_MAX_FILE_BYTES,
    chunk_text,
    max_file_bytes_from_env,
    validate_dropbox_root,
    validate_embedding_vectors,
    validate_file_size,
)


class RagIngestSafetyTests(unittest.TestCase):
    def test_dropbox_root_requires_specific_absolute_folder(self):
        self.assertEqual(
            validate_dropbox_root(" /Institutional_RAG/01_RAW_SOURCES "),
            "/Institutional_RAG/01_RAW_SOURCES",
        )
        for value in ("", "relative/folder", "/", "/folder/../other"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_dropbox_root(value)

    def test_max_file_bytes_has_safe_default_and_rejects_invalid_values(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(max_file_bytes_from_env(), DEFAULT_MAX_FILE_BYTES)
        for value in ("0", "-10", "large"):
            with patch.dict("os.environ", {"MAX_FILE_BYTES": value}, clear=True):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    max_file_bytes_from_env()

    def test_file_size_limit_rejects_oversized_source(self):
        validate_file_size("/source.txt", 10, 10)
        with self.assertRaisesRegex(ValueError, "MAX_FILE_BYTES"):
            validate_file_size("/source.txt", 11, 10)

    def test_embedding_vectors_require_expected_dimension_and_finite_values(self):
        validate_embedding_vectors([[0.0] * 384])
        with self.assertRaisesRegex(ValueError, "dimension mismatch"):
            validate_embedding_vectors([[0.0] * 3])
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_embedding_vectors([[float("nan")] + [0.0] * 383])
        with self.assertRaisesRegex(ValueError, "no vectors"):
            validate_embedding_vectors([])

    def test_chunking_handles_empty_unicode_and_overlap(self):
        self.assertEqual(chunk_text("   ", 10, 2), [])
        text = "Halo 世界 " * 20
        chunks = chunk_text(text, 24, 4)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.strip() for chunk in chunks))
        self.assertTrue(all(len(chunk) <= 24 for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
