"""GitHub write actions via the official gh CLI.

forgebot never handles tokens: gh manages its own authentication
(`gh auth login`), and every call is an argv list — never a shell string.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class GitHubError(RuntimeError):
    pass


def gh_path() -> str:
    path = shutil.which("gh")
    if path is None:
        raise GitHubError(
            "gh CLI not found. Install it from https://cli.github.com "
            "and run `gh auth login`."
        )
    return path


def run_gh(argv: list[str], cwd: Path, timeout: float = 120.0) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        [gh_path(), *argv], cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    if proc.returncode != 0:
        raise GitHubError(
            f"gh {argv[0]} {argv[1]} failed with exit code {proc.returncode}: "
            f"{(proc.stderr or proc.stdout).strip()[:400]}"
        )
    return proc


def comment_argv(payload: dict) -> list[str]:
    argv = ["issue", "comment", str(payload["number"]), "--body", payload["body"]]
    if payload.get("repo"):
        argv += ["--repo", str(payload["repo"])]
    return argv
