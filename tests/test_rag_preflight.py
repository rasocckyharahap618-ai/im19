import tempfile
import unittest
from pathlib import Path

from scripts.rag_preflight import REQUIRED_CONFIG, REQUIRED_FILES, configured_names


class RagPreflightTests(unittest.TestCase):
    def test_env_values_are_not_needed_for_file_check_and_empty_values_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text(
                "DROPBOX_ACCESS_TOKEN=abc123\n"
                "SUPABASE_URL=\n"
                "SUPABASE_SERVICE_ROLE_KEY='   '\n",
                encoding="utf-8",
            )
            found = configured_names(root, env={})
            self.assertEqual(found, {"DROPBOX_ACCESS_TOKEN"})
            self.assertTrue(found.issubset(set(REQUIRED_CONFIG)))

    def test_nonempty_environment_setting_is_detected_without_returning_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            found = configured_names(root, env={"SUPABASE_URL": "https://example.invalid"})
            self.assertEqual(found, {"SUPABASE_URL"})
            self.assertNotIn("https://example.invalid", repr(found))

    def test_required_file_list_includes_runtime_and_migration(self):
        self.assertIn("integrations/rag/ingest.py", REQUIRED_FILES)
        self.assertIn("integrations/rag/retrieve.py", REQUIRED_FILES)
        self.assertTrue(any(path.startswith("supabase/migrations/") for path in REQUIRED_FILES))


if __name__ == "__main__":
    unittest.main()
