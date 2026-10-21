"""IM 19 restricted MCP server for a Codespaces workspace.

Run this server through stdio and connect it with OpenAI Secure MCP Tunnel.
It exposes fixed tools, not a generic shell. It does not deploy or push changes.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from integrations.remote_control.policy import (
    MAX_FILE_BYTES,
    PolicyError,
    require_work_branch,
    safe_repo_path,
    validate_patch,
)

ROOT = Path(os.environ.get("IM19_WORKSPACE", Path.cwd())).resolve()
mcp = FastMCP(
    "IM 19 Codespaces Remote Control",
    instructions=(
        "Use only the provided narrow tools. Never request secrets. "
        "Writes are limited to allowlisted files on agent/* or work/* branches. "
        "Do not deploy, push, alter workflow permissions, or run arbitrary commands."
    ),
)


def _run_git(*args: str, timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _current_branch() -> str:
    result = _run_git("branch", "--show-current")
    if result.returncode != 0:
        raise RuntimeError("Unable to determine the current Git branch.")
    return result.stdout.strip()


def _ensure_workspace() -> None:
    if not (ROOT / ".git").exists() and not (ROOT / ".git").is_file():
        raise RuntimeError("IM19_WORKSPACE must point to a Git working tree.")


@mcp.tool()
def workspace_status() -> dict:
    """Return branch, commit, and a bounded Git status; no file contents or secrets."""
    _ensure_workspace()
    branch = _current_branch()
    commit = _run_git("rev-parse", "--short", "HEAD")
    status = _run_git("status", "--short", "--branch")
    if commit.returncode or status.returncode:
        raise RuntimeError("Git status check failed.")
    return {
        "workspace": ROOT.name,
        "branch": branch,
        "commit": commit.stdout.strip(),
        "status": status.stdout[:12000],
        "write_allowed": branch.startswith(("agent/", "work/")),
        "deploy_enabled": False,
    }


@mcp.tool()
def read_project_file(path: str) -> dict:
    """Read a small text file only from allowlisted source/test/docs directories."""
    _ensure_workspace()
    relative = safe_repo_path(path)
    target = (ROOT / relative).resolve()
    if ROOT not in target.parents:
        raise PolicyError("Resolved path escapes the workspace.")
    if not target.is_file():
        raise FileNotFoundError("File does not exist.")
    if target.stat().st_size > MAX_FILE_BYTES:
        raise PolicyError("File exceeds the 32 KiB read limit.")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PolicyError("Only UTF-8 text files can be read.") from exc
    return {"path": relative, "content": content}


@mcp.tool()
def run_unit_tests() -> dict:
    """Run the fixed offline unit-test command; arbitrary commands are not accepted."""
    _ensure_workspace()
    result = subprocess.run(
        ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "TOKENIZERS_PARALLELISM": "false"},
    )
    return {
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout[-12000:],
        "stderr": result.stderr[-12000:],
        "command": "python -m unittest discover -s tests -v",
    }


@mcp.tool()
def apply_unified_patch(patch: str) -> dict:
    """Apply a reviewed unified diff on an agent/* or work/* branch only.

    This tool never commits, pushes, merges, deploys, or changes GitHub Actions.
    """
    _ensure_workspace()
    branch = _current_branch()
    require_work_branch(branch)
    changed_paths = validate_patch(patch)
    checked = subprocess.run(
        ["git", "-C", str(ROOT), "apply", "--check", "--"],
        input=patch,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if checked.returncode:
        return {
            "applied": False,
            "branch": branch,
            "changed_paths": changed_paths,
            "error": (checked.stderr or checked.stdout)[-4000:],
        }
    applied = subprocess.run(
        ["git", "-C", str(ROOT), "apply", "--"],
        input=patch,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    return {
        "applied": applied.returncode == 0,
        "branch": branch,
        "changed_paths": changed_paths,
        "error": (applied.stderr or applied.stdout)[-4000:] if applied.returncode else "",
        "next_step": "Run run_unit_tests and inspect git diff before any commit.",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
