import unittest
from integrations.rag.evaluation import aggregate_metrics, evaluate_case, precision_at_k, recall_at_k
from integrations.rag.mining import assess_document, build_provenance, chunk_text, normalize_text, sha256_text

class InstitutionalMiningTests(unittest.TestCase):
    def test_normalization_is_stable(self):
        self.assertEqual(normalize_text(" A  B\r\n\r\n\r\nC "), "A B\n\nC")
        self.assertEqual(sha256_text("A  B"), sha256_text("A B"))
    def test_quality_rejects_empty_and_short(self):
        self.assertFalse(assess_document("").accepted)
        self.assertIn("below_minimum_character_count", assess_document("too short").reasons)
    def test_quality_accepts_meaningful_document(self):
        text = "Institutional knowledge retrieval needs provenance, citations, evaluation, and access controls. " * 4
        report = assess_document(text)
        self.assertTrue(report.accepted)
        self.assertEqual(len(report.content_hash), 64)
    def test_chunking_empty_and_overlap_validation(self):
        self.assertEqual(chunk_text("  "), [])
        with self.assertRaises(ValueError):
            chunk_text("x" * 300, chunk_size=100, overlap=100)
    def test_chunking_is_deterministic_and_bounded(self):
        text = "Paragraph about retrieval, citations, and provenance. " * 60
        first = chunk_text(text, chunk_size=300, overlap=40)
        self.assertEqual(first, chunk_text(text, chunk_size=300, overlap=40))
        self.assertGreater(len(first), 1)
        self.assertTrue(all(item["content"] for item in first))
        self.assertEqual([x["chunk_index"] for x in first], list(range(len(first))))
    def test_provenance_contains_hash_and_pipeline_version(self):
        text = "Institutional RAG provenance tracks source identity and source versions. " * 3
        record = build_provenance(source_uri="dropbox:///manual.md", source_version="v3", title="Manual", text=text)
        self.assertEqual(len(record["content_hash"]), 64)
        self.assertEqual(record["pipeline_version"], "im19-institutional-rag-mining-v1")
    def test_precision_recall(self):
        self.assertEqual(precision_at_k(["a", "b", "c"], {"a", "c"}, 2), 0.5)
        self.assertEqual(recall_at_k(["a", "b", "c"], {"a", "c"}, 2), 0.5)
    def test_case_and_aggregate_metrics(self):
        case = {"id": "eval-1", "query": "source governance", "relevant_source_uris": ["doc://policy"]}
        results = [{"source_uri": "doc://other", "content": "irrelevant"}, {"source_uri": "doc://policy", "content": "policy"}]
        row = evaluate_case(case, results, k=2)
        self.assertEqual(row["reciprocal_rank"], 0.5)
        aggregate = aggregate_metrics([row])
        self.assertEqual(aggregate["case_count"], 1)
        self.assertEqual(aggregate["source_hit_rate"], 1.0)

if __name__ == "__main__":
    unittest.main()
