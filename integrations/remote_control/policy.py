"""Safety policy for the IM 19 Codespaces MCP tools.

This module deliberately exposes a narrow set of operations. It never accepts
an arbitrary shell command and never permits writes to the default branch.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath

MAX_PATCH_BYTES = 64 * 1024
MAX_FILE_BYTES = 32 * 1024
ALLOWED_READ_ROOTS = ("integrations/", "tests/", "scripts/", "docs/")
ALLOWED_PATCH_ROOTS = ("integrations/rag/", "tests/", "scripts/", "docs/")
DENIED_PARTS = {".git", ".venv", "venv", "__pycache__", "node_modules"}
DENIED_NAMES = {
    ".env", ".env.local", ".env.production", "credentials.json",
    "service-account.json", "id_rsa", "id_ed25519",
}
SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsb_secret_[A-Za-z0-9_\-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class PolicyError(ValueError):
    """Raised when a requested operation violates the remote-control policy."""


def safe_repo_path(raw_path: str, *, for_write: bool = False) -> str:
    """Return a normalized repository-relative path or reject it."""
    if not raw_path or "\x00" in raw_path or "\\" in raw_path:
        raise PolicyError("Invalid repository path.")
    path = PurePosixPath(raw_path)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise PolicyError("Path must be a normalized relative path without traversal.")
    if any(part in DENIED_PARTS for part in path.parts):
        raise PolicyError("Access to internal/runtime directories is blocked.")
    if path.name in DENIED_NAMES or path.name.startswith(".env"):
        raise PolicyError("Access to secret/configuration files is blocked.")
    normalized = path.as_posix()
    roots = ALLOWED_PATCH_ROOTS if for_write else ALLOWED_READ_ROOTS
    if not normalized.startswith(roots):
        raise PolicyError("Path is outside the allowlisted repository areas.")
    return normalized


def validate_patch(patch: str) -> list[str]:
    """Validate a unified diff and return its changed repository paths."""
    if not isinstance(patch, str) or not patch.strip():
        raise PolicyError("Patch must be a non-empty unified diff.")
    if len(patch.encode("utf-8")) > MAX_PATCH_BYTES:
        raise PolicyError("Patch exceeds the 64 KiB limit.")
    if any(pattern.search(patch) for pattern in SECRET_PATTERNS):
        raise PolicyError("Patch appears to contain a credential or private key.")
    if "\x00" in patch:
        raise PolicyError("Binary patches are not allowed.")

    paths: list[str] = []
    for line in patch.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            raw = line[4:].split("\t", 1)[0]
            if raw == "/dev/null":
                continue
            if raw.startswith("a/") or raw.startswith("b/"):
                raw = raw[2:]
            paths.append(safe_repo_path(raw, for_write=True))
    if not paths:
        raise PolicyError("Patch contains no recognizable file paths.")
    return sorted(set(paths))


def require_work_branch(branch: str) -> None:
    """Reject default/protected branches and require an agent/work branch."""
    if branch in {"main", "master", "production", "prod"}:
        raise PolicyError("Writes are disabled on protected/default branches.")
    if not (branch.startswith("agent/") or branch.startswith("work/")):
        raise PolicyError("Switch to an agent/* or work/* branch before writing.")
