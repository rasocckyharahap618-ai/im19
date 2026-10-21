import os
import unittest
from unittest.mock import patch

from integrations.rag.config import require_supabase_config


class SupabaseConfigTests(unittest.TestCase):
    def test_valid_project_url_is_returned_without_trailing_slash(self):
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://example.supabase.co/",
            "SUPABASE_SERVICE_ROLE_KEY": "server-key-placeholder",
        }, clear=False):
            self.assertEqual(
                require_supabase_config(),
                ("https://example.supabase.co", "server-key-placeholder"),
            )

    def test_url_with_rest_path_is_rejected(self):
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://example.supabase.co/rest/v1",
            "SUPABASE_SERVICE_ROLE_KEY": "server-key-placeholder",
        }, clear=False):
            with self.assertRaisesRegex(RuntimeError, "base project URL"):
                require_supabase_config()

    def test_malformed_url_is_rejected_without_echoing_value(self):
        bad_url = "not a URL"
        with patch.dict(os.environ, {
            "SUPABASE_URL": bad_url,
            "SUPABASE_SERVICE_ROLE_KEY": "server-key-placeholder",
        }, clear=False):
            with self.assertRaises(RuntimeError) as error:
                require_supabase_config()
            self.assertNotIn(bad_url, str(error.exception))

    def test_missing_key_is_reported(self):
        with patch.dict(os.environ, {"SUPABASE_URL": "https://example.supabase.co"}, clear=False):
            with patch.dict(os.environ, {"SUPABASE_SERVICE_ROLE_KEY": ""}):
                with self.assertRaisesRegex(RuntimeError, "SUPABASE_SERVICE_ROLE_KEY is missing"):
                    require_supabase_config()


if __name__ == "__main__":
    unittest.main()
