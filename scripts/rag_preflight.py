#!/usr/bin/env python3
"""Offline preflight checks for the IM 19 RAG workspace.

This tool never prints secret values, contacts external services, or changes Git state.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = (
    "integrations/rag/__init__.py",
    "integrations/rag/README.md",
    "integrations/rag/healthcheck.py",
    "integrations/rag/ingest.py",
    "integrations/rag/retrieve.py",
    "integrations/rag/requirements.txt",
    "supabase/migrations/20261021000000_institutional_rag_connectors.sql",
)
REQUIRED_CONFIG = (
    "DROPBOX_ACCESS_TOKEN",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
)


def configured_names(root: Path, env: dict[str, str] | None = None) -> set[str]:
    """Return only names of required settings with non-empty values; never values."""
    source = os.environ if env is None else env
    configured = {name for name in REQUIRED_CONFIG if source.get(name, "").strip()}
    env_file = root / ".env"
    if not env_file.is_file():
        return configured

    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return configured

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1].strip()
        if key in REQUIRED_CONFIG and value:
            configured.add(key)
    return configured


def run_git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-config",
        action="store_true",
        help="exit non-zero if any required setting is missing or empty",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    print("IM 19 RAG preflight (offline; no state changes)")
    print(f"Workspace: {root}")

    git_root = run_git(root, "rev-parse", "--show-toplevel")
    if git_root:
        print(f"Git root:  {git_root}")
        branch = run_git(root, "branch", "--show-current")
        head = run_git(root, "rev-parse", "--short", "HEAD")
        origin_main = run_git(root, "rev-parse", "--short", "--verify", "origin/main")
        print(f"Branch:    {branch or '(detached HEAD or unavailable)'}")
        print(f"HEAD:      {head or '(unavailable)'}")
        if origin_main:
            print(f"origin/main (local tracking ref): {origin_main}")
            if head and head != origin_main:
                print("NOTE: HEAD and the locally cached origin/main ref differ; this alone does not prove which is newer.")
    else:
        print("ERROR: current workspace is not inside a Git repository.")
        return 2

    missing = [rel for rel in REQUIRED_FILES if not (root / rel).is_file()]
    if missing:
        print("\nERROR: required repository files are missing:")
        for rel in missing:
            print(f"  - {rel}")
        print("\nSafe recovery:")
        print("  1. Inspect: git status --short --branch")
        print("  2. Refresh refs: git fetch origin")
        print("  3. Inspect status again. Preserve any local changes.")
        print("  4. Only with a clean working tree on main: git pull --ff-only origin main")
        print("Do not use git reset --hard to fix this issue.")
    else:
        print(f"Files:     OK ({len(REQUIRED_FILES)} required files found)")

    configured = configured_names(root)
    missing_config = [name for name in REQUIRED_CONFIG if name not in configured]
    print("\nRequired configuration (names only; values are never displayed):")
    for name in REQUIRED_CONFIG:
        print(f"  {name}: {'present' if name in configured else 'MISSING/EMPTY'}")
    if missing_config:
        print("NOTE: network health checks cannot succeed until missing settings are provided securely.")

    if missing:
        return 2
    if args.strict_config and missing_config:
        return 3
    print("\nPreflight passed. This checks local files/configuration only; it does not prove live service connectivity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
