"""Credential-free unit tests for ingestion primitives."""
import unittest

from integrations.rag.ingest import chunk_text, extract_text


class ChunkTextTests(unittest.TestCase):
    def test_empty_text_returns_no_chunks(self):
        self.assertEqual(chunk_text("   ", 20, 2), [])

    def test_short_text_is_one_chunk(self):
        self.assertEqual(chunk_text("hello world", 100, 10), ["hello world"])

    def test_long_text_chunks_and_overlap(self):
        source = " ".join(f"word{i}" for i in range(30))
        chunks = chunk_text(source, 35, 8)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunks))
        self.assertEqual(" ".join(chunks).replace("  ", " ")[:5], "word0")
        # Every chunk remains bounded except for a single word longer than the limit.
        self.assertTrue(all(len(chunk) <= 35 for chunk in chunks))

    def test_invalid_chunk_settings_raise(self):
        for size, overlap in [(0, 0), (10, -1), (10, 10)]:
            with self.subTest(size=size, overlap=overlap):
                with self.assertRaises(ValueError):
                    chunk_text("some content", size, overlap)


class ExtractTextTests(unittest.TestCase):
    def test_plain_text_utf8(self):
        self.assertEqual(extract_text("source.txt", "Halo dunia".encode()), "Halo dunia")

    def test_html_extracts_visible_text(self):
        result = extract_text("source.html", b"<html><title>Title</title><body><p>Isi dokumen</p></body></html>")
        self.assertIn("Isi dokumen", result)

    def test_unsupported_extension_returns_empty(self):
        self.assertEqual(extract_text("source.csv", b"a,b"), "")


if __name__ == "__main__":
    unittest.main()
