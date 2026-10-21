import unittest

from integrations.remote_control.policy import (
    PolicyError,
    require_work_branch,
    safe_repo_path,
    validate_patch,
)


class RemoteControlPolicyTests(unittest.TestCase):
    def test_read_path_allows_source(self):
        self.assertEqual(safe_repo_path("integrations/rag/ingest.py"), "integrations/rag/ingest.py")

    def test_blocks_traversal(self):
        with self.assertRaises(PolicyError):
            safe_repo_path("integrations/rag/../../.env")

    def test_blocks_env_and_git(self):
        for path in (".env", "integrations/.env.production", "integrations/.git/config"):
            with self.subTest(path=path), self.assertRaises(PolicyError):
                safe_repo_path(path)

    def test_patch_only_allows_reviewable_paths(self):
        patch = (
            "--- a/tests/example.py\n"
            "+++ b/tests/example.py\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n"
        )
        self.assertEqual(validate_patch(patch), ["tests/example.py"])

    def test_patch_rejects_workflow_edits(self):
        patch = "--- a/.github/workflows/deploy.yml\n+++ b/.github/workflows/deploy.yml\n"
        with self.assertRaises(PolicyError):
            validate_patch(patch)

    def test_patch_rejects_credentials(self):
        patch = (
            "--- a/tests/example.py\n+++ b/tests/example.py\n"
            "+ghp_abcdefghijklmnopqrstuvwxyz1234567890ABCDE\n"
        )
        with self.assertRaises(PolicyError):
            validate_patch(patch)

    def test_protected_branch_is_rejected(self):
        with self.assertRaises(PolicyError):
            require_work_branch("main")

    def test_only_agent_or_work_branch_is_allowed(self):
        require_work_branch("agent/chatgpt-work")
        require_work_branch("work/rag-fix")
        with self.assertRaises(PolicyError):
            require_work_branch("feature/random")


if __name__ == "__main__":
    unittest.main()
